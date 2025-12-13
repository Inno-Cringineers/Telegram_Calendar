import asyncio
from datetime import UTC, datetime, time, timedelta, timezone

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.database import UnitOfWork
from handlers.daily_plan import get_event_duration, get_event_recurrence_info, get_event_source
from i18n.strings import t
from logger.logger import logger
from repositories.schemas import EventDurationFilter
from store.store import Store
from utils.handlers import parse_user_timezone


class DailyPlanScheduler:
    """
    Maintains a per-user asyncio Task which sleeps until the next daily plan and sends it.
    You must call `start()` on application startup and `stop()` on shutdown.
    On any change to events for a user call `rebuild_user_schedule(user_id)`.
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

    # ---------------- core: select next reminders for a user ----------------

    async def _get_next_daily_plan_for_user(self, user_id: int) -> datetime | None:
        """
        Find next daily plan time for a user.
        Returns None if nothing is scheduled.
        """

        async with UnitOfWork(self.session_maker) as uow:
            session = uow.session
            if session is None:
                raise RuntimeError("Session is None")
            store = Store(session)
            settings = await store.SettingsService.get_by_user_id(user_id)
            if settings is None or not settings.daily_plans_enabled:
                return None

            if settings.daily_plans_time is None:
                return None

            daily_plans_time: time = settings.daily_plans_time
            user_tz = self._parse_timezone(settings.timezone)
            user_date_now = datetime.now(user_tz)

            # if current time > daily plans time, return next day daily plan time
            if user_date_now.time() >= daily_plans_time:
                user_date_now = user_date_now + timedelta(days=1)

            next_daily_plan_time = user_date_now.replace(
                hour=daily_plans_time.hour, minute=daily_plans_time.minute, second=0, microsecond=0
            )
            # return next daily plan time in UTC
            return next_daily_plan_time.astimezone(UTC)

    # ---------------- worker per user ----------------

    async def _user_loop(self, user_id: int) -> None:
        """Main loop for each user: sleep until next daily plan, then send and loop."""

        self._locks.setdefault(user_id, asyncio.Lock())  # lock to prevent concurrent rebuilds

        logger.info("Starting daily plan worker for user %s", user_id)

        try:
            while not self._stop_event.is_set():
                # build next daily plan
                try:
                    next = await self._get_next_daily_plan_for_user(user_id)
                    if next is None:
                        # sleep while rebuild is requested by user
                        await self._stop_event.wait()
                        if self._stop_event.is_set():
                            break
                        continue
                except Exception as e:
                    logger.error("Failed to compute next daily plan for user %s: %s", user_id, e)
                    await asyncio.sleep(60)  # 1 minute backoff TODO: make it configurable
                    continue

                now = self._now_utc()
                wait = (next - now).total_seconds()
                logger.debug("%s Waiting for next daily plan for user %s at %s, wait: %s", now, user_id, next, wait)
                if wait > 0:
                    # sleep but allow cancellation by setting stop_event or by cancelling task
                    try:
                        logger.debug("Waiting for next daily plan for user %s at %s", user_id, next)
                        # logger.debug("Waiting for next daily plan for user %s at %s", user_id, next)
                        await asyncio.wait_for(self._stop_event.wait(), timeout=wait)
                        # stop_event set -> break
                        if self._stop_event.is_set():
                            break
                    except TimeoutError:
                        # timeout expired -> it's time to send daily plan
                        pass

                # double-check time (race conditions)
                now = self._now_utc()
                if next > now + timedelta(seconds=5):  # 5 seconds check TODO: make it configurable
                    # something changed, rebuild immediately TODO
                    continue

                # send daily plan message
                try:
                    await self._send_daily_plan_message(user_id)
                except Exception as e:
                    logger.exception("Failed to send daily plan for user %s: %s", user_id, e)

                # Recalculate next daily plan time after sending (to avoid sending twice)
                # This ensures we get the next day's time
                next = await self._get_next_daily_plan_for_user(user_id)
                if next is None:
                    # sleep while rebuild is requested by user
                    await self._stop_event.wait()
                    if self._stop_event.is_set():
                        break
                    continue

                # small sleep to avoid tight loop
                await asyncio.sleep(0.5)  # 0.5 seconds sleep TODO: make it configurable

        finally:
            logger.info("Stopping daily plan worker for user %s", user_id)

    async def _send_daily_plan_message(self, user_id: int):
        logger.debug("Sending daily plan message for user %s", user_id)
        async with UnitOfWork(self.session_maker) as uow:
            session = uow.session
            if session is None:
                raise RuntimeError("Session is None")
            store = Store(session)
            settings = await store.SettingsService.get_by_user_id(user_id)
            if settings is None or not settings.daily_plans_enabled:
                return

            user_tz = parse_user_timezone(settings.timezone)

            now_local = datetime.now(user_tz)

            local_from = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            local_to = local_from + timedelta(days=1)

            utc_from = local_from.astimezone(UTC)
            utc_to = local_to.astimezone(UTC)

            events = await store.EventService.get_events_in_range(
                EventDurationFilter(user_id=user_id, duration_from=utc_from, duration_to=utc_to)
            )
            if events == []:
                await self.bot.send_message(
                    user_id,
                    text=(
                        f"{t('daily.plan.title', lang=settings.language, today=now_local.strftime('%d.%m.%Y'))}\n\n"
                        f"{t('daily.plan.no.events', lang=settings.language)}"
                    ),
                    parse_mode="HTML",
                )
                return

            await self.bot.send_message(
                user_id,
                text=t("daily.plan.title", lang=settings.language, today=now_local.strftime("%d.%m.%Y")),
                parse_mode="HTML",
            )

            for event in events:
                await self.bot.send_message(
                    user_id,
                    t(
                        "daily.plan.event.content",
                        lang=settings.language,
                        title=event.title or t("daily.plan.event.title.none", lang=settings.language),
                        description=event.description or t("daily.plan.event.description.none", lang=settings.language),
                        duration=get_event_duration(event, user_tz, settings.language),
                        recurrence=get_event_recurrence_info(event, settings.language),
                        source=await get_event_source(event, store, settings.language),
                    ),
                    parse_mode="HTML",
                )

            await self.bot.send_message(
                user_id,
                text=t("daily.plan.end", lang=settings.language),
                parse_mode="HTML",
            )

    # ---------------- public API ----------------

    async def start(self):
        """Start scheduler: rebuild tasks for users who have daily plans (call on app startup)."""
        logger.debug("Daily plan scheduler: starting scheduler")
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
        Call this after any change affecting user's daily plan.
        """
        logger.debug("Daily plan scheduler: rebuilding schedule for user %s", user_id)
        lock = self._locks.setdefault(user_id, asyncio.Lock())
        async with lock:
            # cancel existing
            # logger.debug("Daily plan scheduler: cancelling existing task", extra={"user_id": user_id})
            old = self._tasks.pop(user_id, None)
            if old:
                old.cancel()
                try:
                    await old
                except asyncio.CancelledError:
                    # Expected when cancelling a task - suppress it
                    logger.debug("Daily plan scheduler: task cancelled successfully for user %s", user_id)
                except Exception as e:
                    logger.error("Daily plan scheduler: failed to cancel existing task for user %s: %s", user_id, e)

            # start new task
            # logger.debug("Daily plan scheduler: starting new task", extra={"user_id": user_id})
            task = self.loop.create_task(self._user_loop(user_id))
            self._tasks[user_id] = task

    async def stop(self):
        """Stop scheduler: cancel all tasks."""
        logger.debug("Daily plan scheduler: stopping scheduler")
        self._stop_event.set()
        for task in self._tasks.values():
            task.cancel()
        await asyncio.gather(*self._tasks.values())
        self._tasks.clear()


# singleton
_scheduler: DailyPlanScheduler | None = None


def init_daily_plan_scheduler(session_maker: async_sessionmaker[AsyncSession], bot: Bot) -> DailyPlanScheduler:
    """
    Инициализирует синглтон. Вызывать один раз — при старте приложения.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = DailyPlanScheduler(session_maker, bot)
    return _scheduler


def get_daily_plan_scheduler() -> DailyPlanScheduler:
    """
    Возвращает существующий синглтон.
    Если он ещё не инициализирован — бросает исключение.
    """
    if _scheduler is None:
        raise RuntimeError(
            "DailyPlanScheduler is not initialized! Call init_daily_plan_scheduler(session_maker, bot) first."
        )
    return _scheduler
