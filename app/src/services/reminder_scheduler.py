# reminder_scheduler.py
import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

from aiogram import Bot
from dateutil.rrule import rrulestr
from icalendar.prop import vDuration
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.database import UnitOfWork
from i18n.strings import t
from logger.logger import logger
from repositories.schemas import EventResponse, ReminderFilter, ReminderResponse, SettingsResponse
from store.store import Store
from utils.handlers import parse_user_timezone


@dataclass
class ReminderRow:
    id: int
    event_id: int


class ReminderScheduler:
    """
    Maintains a per-user asyncio Task which sleeps until the next reminder(s) and sends them.
    You must call `start()` on application startup and `stop()` on shutdown.
    On any change to events/reminders for a user call `rebuild_user_schedule(user_id)`.
    """

    def __init__(
        self, session_maker: async_sessionmaker[AsyncSession], bot: Bot, loop: asyncio.AbstractEventLoop | None = None
    ):
        """
        :param session_maker: async_sessionmaker that will be used to create a Store.
        :param bot: aiogram Bot instance (or any object exposing send_message)
        """
        self.session_maker = session_maker
        self.bot = bot
        self.loop = loop or asyncio.get_event_loop()

        # user -> asyncio.Task
        self._tasks: dict[int, asyncio.Task] = {}
        # per-user locks to prevent concurrent rebuilds
        self._locks: dict[int, asyncio.Lock] = {}
        # cancellation event for whole scheduler
        self._stop_event = asyncio.Event()

    # ---------------- utilities ----------------

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def _parse_timezone(tz_str: str) -> timezone:
        """
        Convert strings like 'UTC+3', 'UTC+5:30', 'UTC-4:45' -> timezone object.
        """
        if not tz_str.startswith("UTC"):
            raise ValueError("Invalid timezone format")

        if tz_str == "UTC":
            return UTC

        sign = 1 if "+" in tz_str else -1
        _, offset_str = tz_str.split("UTC")[1].split(sign == 1 and "+" or "-")

        if ":" in offset_str:
            hours, minutes = map(int, offset_str.split(":"))
        else:
            hours, minutes = int(offset_str), 0

        return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))

    @staticmethod
    def _to_timedelta_from_trigger(trigger_str: str) -> timedelta:
        """
        Parse trigger string:
         - RFC5545 durations like '-PT30M', 'P1D' -> timedelta (can be negative)
        """

        # vDuration.from_ical returns a vDuration-like object; calling it returns timedelta
        # e.g. vDuration.from_ical('-PT30M')() -> timedelta(-, 0, ...)
        td = vDuration.from_ical(trigger_str)
        return td

    # ---------------- recurrence helpers ----------------

    @staticmethod
    def _event_occurrence_after(event: EventResponse, after: datetime) -> datetime | None:
        """
        Return next occurrence start datetime (UTC-aware) for event after given datetime.
        Considers:
        - DTSTART (event.date_start)
        - RRULE
        - RDATE
        - EXDATE
        """
        # --- Base DTSTART ---
        start = event.date_start

        # Collect candidate occurrences
        candidates: list[datetime] = []

        # 1) If DTSTART itself is in the future
        if start > after:
            candidates.append(start)

        # --- RRULE ---
        if event.rrule:
            try:
                rule = rrulestr(event.rrule, dtstart=event.date_start)
                next_rrule = rule.after(after, inc=False)
                if next_rrule:
                    candidates.append(next_rrule.replace(tzinfo=UTC))  # TODO: check if tzinfo is needed here
            except Exception as e:
                logger.error("Failed parsing RRULE %s: %s", event.rrule, e)

        # --- RDATE ---
        if event.rdate:
            for dt in event.rdate:
                # RDATE is datetime
                if dt > after:
                    candidates.append(dt)

        # --- EXDATE ---
        exdates = set()
        if event.exdate:
            for dt in event.exdate:
                exdates.add(dt)

        # Filter out EXDATE
        candidates = [c for c in candidates if c not in exdates]

        if not candidates:
            return None

        return min(candidates)

    async def _compute_reminder_send_time(self, reminder: ReminderResponse) -> datetime | None:
        """
        Given a reminder, compute the UTC time when reminder should be sent.
        """

        async with UnitOfWork(self.session_maker) as uow:
            session = uow.session
            if session is None:
                raise RuntimeError("Session is None")
            store = Store(session)
            event = await store.EventService.get_by_id(reminder.event_id)
            if event is None:
                return None

            # get next occurrence of event after now
            occur = self._event_occurrence_after(event, self._now_utc())
            if occur is None:
                return None
            return occur - self._to_timedelta_from_trigger(reminder.trigger_offset)

    # ---------------- core: select next reminders for a user ----------------

    async def _get_next_reminders_for_user(self, user_id: int) -> tuple[datetime, list[int]] | None:
        """
        Find next trigger time and corresponding reminders for a user.
        Returns None if nothing is scheduled.
        """
        now = self._now_utc()

        async with UnitOfWork(self.session_maker) as uow:
            session = uow.session
            if session is None:
                raise RuntimeError("Session is None")
            store = Store(session)
            # getting reminders for the user
            reminders = await store.ReminderService.find(ReminderFilter(user_id=user_id))
            if not reminders:
                return None

            # candidates to send reminders {send_at, list[reminder_id]}
            send_candidates: dict[datetime, list[int]] = {}

            # getting events for the reminders
            for reminder in reminders:
                # compute when reminder should be sent
                send_at = await self._compute_reminder_send_time(reminder)
                if send_at is None or send_at < now:
                    continue

                # add to send_candidates
                send_candidates.setdefault(send_at, []).append(reminder.id)

            if not send_candidates:
                return None

            # choose earliest send_at
            earliest = min(send_candidates.keys())
            return earliest, send_candidates[earliest]

    # ---------------- worker per user ----------------

    async def _user_loop(self, user_id: int) -> None:
        """Main loop for each user: sleep until next trigger, then send and loop."""

        self._locks.setdefault(user_id, asyncio.Lock())  # lock to prevent concurrent rebuilds

        logger.info("Starting reminder worker for user %s", user_id)

        try:
            while not self._stop_event.is_set():
                # build next reminders
                try:
                    next = await self._get_next_reminders_for_user(user_id)
                    if next is None:
                        # sleep while rebuild is requested by user
                        await self._stop_event.wait()
                        if self._stop_event.is_set():
                            break
                        continue
                    next_send_at = next[0]
                    next_reminder_ids = next[1]
                except Exception as e:
                    logger.error("Failed to compute next reminders for user %s: %s", user_id, e)
                    await asyncio.sleep(60)  # 1 minute backoff TODO: make it configurable
                    continue

                now = self._now_utc()
                wait = (next_send_at - now).total_seconds()
                if wait > 0:
                    # sleep but allow cancellation by setting stop_event or by cancelling task
                    try:
                        logger.debug("Waiting for next reminders for user %s at %s", user_id, next_send_at)
                        await asyncio.wait_for(self._stop_event.wait(), timeout=wait)
                        # stop_event set -> break
                        if self._stop_event.is_set():
                            break
                    except TimeoutError:
                        # timeout expired -> it's time to send reminders
                        pass

                # double-check time (race conditions)
                now = self._now_utc()
                if next_send_at > now + timedelta(seconds=5):  # 5 seconds check TODO: make it configurable
                    # something changed, rebuild immediately TODO
                    continue

                # send all reminders for this trigger time
                for reminder_id in next_reminder_ids:
                    try:
                        await self._send_reminder_message(user_id, reminder_id)
                    except Exception as e:
                        logger.exception("Failed to send reminder %s: %s", reminder_id, e)

                # small sleep to avoid tight loop if many reminders are at same second
                await asyncio.sleep(0.5)  # 0.5 seconds sleep TODO: make it configurable

        finally:
            logger.info("Stopping reminder worker for user %s", user_id)

    async def _send_reminder_message(self, user_id: int, reminder_id: int):
        logger.debug("Sending reminder message for user %s, reminder_id: %s", user_id, reminder_id)
        async with UnitOfWork(self.session_maker) as uow:
            session = uow.session
            if session is None:
                raise RuntimeError("Session is None")
            store = Store(session)
            reminder = await store.ReminderService.get_by_id(reminder_id)
            if reminder is None:
                return
            event = await store.EventService.get_by_id(reminder.event_id)
            if event is None:
                return
            settings = await store.SettingsService.get_by_user_id(user_id)
            if settings is None:
                return
        name = self._format_name(event.title, settings)
        start = self._format_start(event.date_start, settings)
        message = t("reminder.message", event_name=name, start=start, lang=settings.language)

        await self.bot.send_message(user_id, message, parse_mode="HTML")

    @staticmethod
    def _format_name(name: str | None, settings: SettingsResponse) -> str:
        if name is None:
            return t("event.title.none", lang=settings.language)
        return name

    @staticmethod
    def _format_start(start: datetime, settings: SettingsResponse) -> str:
        tz_info = parse_user_timezone(settings.timezone)
        return start.astimezone(tz_info).strftime("%d.%m.%Y %H:%M")

    # ---------------- public API ----------------

    async def start(self):
        """Start scheduler: rebuild tasks for users who have reminders (call on app startup)."""
        logger.debug("Reminder scheduler: starting scheduler")
        self._stop_event.clear()
        # gather users
        user_ids = []
        async with UnitOfWork(self.session_maker) as uow:
            session = uow.session
            if session is None:
                raise RuntimeError("Session is None")
            store = Store(session)
            user_ids = await store.SettingsService.get_all_users()
        for user_id in user_ids:
            await self.rebuild_user_schedule(user_id)

    async def rebuild_user_schedule(self, user_id: int):
        """
        Cancel existing task for user (if any) and start a new worker.
        Call this after any change affecting user's reminders.
        """
        logger.debug("Reminder scheduler: rebuilding schedule for user %s", user_id)
        lock = self._locks.setdefault(user_id, asyncio.Lock())
        async with lock:
            # cancel existing
            # logger.debug("Reminder scheduler: cancelling existing task", extra={"user_id": user_id})
            old = self._tasks.pop(user_id, None)
            if old:
                old.cancel()
                try:
                    await old
                except asyncio.CancelledError:
                    # Expected when cancelling a task - suppress it
                    logger.debug("Reminder scheduler: task cancelled successfully for user %s", user_id)
                except Exception as e:
                    logger.error("Failed to cancel existing task for user %s: %s", user_id, e)

            # start new task
            # logger.debug("Reminder scheduler: starting new task", extra={"user_id": user_id})
            task = self.loop.create_task(self._user_loop(user_id))
            self._tasks[user_id] = task

    async def stop(self):
        """Stop scheduler: cancel all tasks."""
        logger.debug("Reminder scheduler: stopping scheduler")
        self._stop_event.set()
        for task in self._tasks.values():
            task.cancel()
        await asyncio.gather(*self._tasks.values())
        self._tasks.clear()
