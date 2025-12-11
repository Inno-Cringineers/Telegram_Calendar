from datetime import UTC, datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from dateutil.rrule import rrulestr

from i18n.strings import t
from keyboards.inline import back_button
from logger.logger import logger
from repositories.schemas import EventDurationFilter, EventResponse
from store.store import Store
from utils.handlers import edit_message, parse_user_timezone, send_message

router = Router()


@router.callback_query(F.data == "menu_daily_plan")
async def get_daily_plan(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Send daily plan to user."""
    user_id = query.from_user.id

    settings = await store.SettingsService.get_by_user_id(user_id)
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
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            text=(
                f"{t('daily.plan.title', lang=lang, today=now_local.strftime('%d.%m.%Y'))}\n\n"
                f"{t('daily.plan.no.events', lang=lang)}"
            ),
            reply_markup=back_button("back_to_main", lang=lang),
            parse_mode="HTML",
            delete_keyboard=True,
        )
        return

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=t("daily.plan.title", lang=lang, today=now_local.strftime("%d.%m.%Y")),
        reply_markup=None,
        parse_mode="HTML",
        delete_keyboard=False,
        delete_message=True,
    )

    for event in events:
        await send_message(
            query.bot,
            query.message.chat.id,
            state,
            t(
                "daily.plan.event.content",
                lang=lang,
                title=event.title or t("daily.plan.event.title.none", lang=lang),
                description=event.description or t("daily.plan.event.description.none", lang=lang),
                duration=get_event_duration(event, user_tz, lang),
                recurrence=get_event_recurrence_info(event, lang),
                source=await get_event_source(event, store, lang),
            ),
            parse_mode="HTML",
            delete_keyboard=False,
            delete_message=True,
        )

    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        t("daily.plan.end", lang=lang),
        reply_markup=back_button("back_to_main", lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
        delete_message=False,
    )


def _get_next_occurrence_date(event: EventResponse, tz_info: timezone) -> datetime:
    """Get the next occurrence date for a recurring event, or current date if event occurs today.

    For all_day events, compares only dates (not times).
    For regular events, compares full datetime.

    Args:
        event: Event to get occurrence for.
        tz_info: User's timezone.

    Returns:
        Next occurrence datetime in UTC, or event.date_start if not recurring.
    """
    now_utc = datetime.now(UTC)
    now_local = now_utc.astimezone(tz_info)

    # If event is not recurring, return original date_start
    if not event.rrule and not event.rdate:
        return event.date_start

    # For all_day events, we need to compare dates only
    if event.all_day:
        # Get current date at midnight in user's timezone
        today_start = datetime.combine(now_local.date(), datetime.min.time()).replace(tzinfo=tz_info)
        today_start_utc = today_start.astimezone(UTC)

        # Find all occurrences (including today if it matches)
        all_day_candidates: list[datetime] = []

        # Check base DTSTART
        event_date_local = event.date_start.astimezone(tz_info).date()
        if event_date_local == now_local.date():
            all_day_candidates.append(event.date_start)
        elif event.date_start > today_start_utc:
            all_day_candidates.append(event.date_start)

        # Check RRULE
        if event.rrule:
            try:
                rule = rrulestr(event.rrule, dtstart=event.date_start)
                # For all_day, we want occurrences from today onwards (inclusive)
                next_rrule = rule.after(today_start_utc, inc=True)
                if next_rrule:
                    # Ensure timezone is UTC
                    if next_rrule.tzinfo is None:
                        next_rrule = next_rrule.replace(tzinfo=UTC)
                    # Check if it's today or later
                    if next_rrule.astimezone(tz_info).date() >= now_local.date():
                        all_day_candidates.append(next_rrule)
            except Exception as e:
                logger.error("Failed parsing RRULE %s: %s", event.rrule, e)

        # Check RDATE
        if event.rdate:
            for dt in event.rdate:
                if dt.astimezone(tz_info).date() >= now_local.date():
                    all_day_candidates.append(dt)

        # Filter out EXDATE
        exdates = set()
        if event.exdate:
            for dt in event.exdate:
                exdates.add(dt)

        all_day_candidates = [c for c in all_day_candidates if c not in exdates]

        if all_day_candidates:
            # If any occurrence is today, return today's date
            for candidate in all_day_candidates:
                if candidate.astimezone(tz_info).date() == now_local.date():
                    return today_start_utc
            # Otherwise return the earliest future occurrence
            return min(all_day_candidates)

        return event.date_start
    else:
        # For regular events, compare full datetime
        regular_candidates: list[datetime] = []

        # Check if event is happening now or in the future
        if event.date_start >= now_utc:
            regular_candidates.append(event.date_start)

        # Check RRULE
        if event.rrule:
            try:
                rule = rrulestr(event.rrule, dtstart=event.date_start)
                # Include current time if event is happening now
                next_rrule = rule.after(now_utc, inc=True)
                if next_rrule:
                    if next_rrule.tzinfo is None:
                        next_rrule = next_rrule.replace(tzinfo=UTC)
                    regular_candidates.append(next_rrule)
            except Exception as e:
                logger.error("Failed parsing RRULE %s: %s", event.rrule, e)

        # Check RDATE
        if event.rdate:
            for dt in event.rdate:
                if dt >= now_utc:
                    regular_candidates.append(dt)

        # Filter out EXDATE
        regular_exdates = set()
        if event.exdate:
            for dt in event.exdate:
                regular_exdates.add(dt)

        regular_candidates = [c for c in regular_candidates if c not in regular_exdates]

        if regular_candidates:
            return min(regular_candidates)

        return event.date_start


def get_event_recurrence_info(event: EventResponse, lang: str) -> str:
    """Format event recurrence information for display.
    
    Args:
        event: Event to get recurrence info for.
        lang: Language code.
        
    Returns:
        Formatted recurrence string, or empty string if event doesn't repeat.
    """
    # Check if event has RDATE only (no RRULE)
    if event.rdate and not event.rrule:
        count = len(event.rdate)
        if count == 1:
            return t("daily.plan.event.recurrence.rdate.single", lang=lang)
        return t("daily.plan.event.recurrence.rdate.multiple", lang=lang, count=count)
    
    # Check if event has RRULE
    if not event.rrule:
        return ""
    
    try:
        # Parse RRULE to extract information
        rule_str = event.rrule.upper()
        
        # Extract FREQ
        if "FREQ=DAILY" in rule_str:
            # Check for interval
            interval = 1
            if "INTERVAL=" in rule_str:
                try:
                    interval_part = rule_str.split("INTERVAL=")[1].split(";")[0]
                    interval = int(interval_part)
                except (ValueError, IndexError):
                    pass
            
            if interval == 1:
                return t("daily.plan.event.recurrence.daily", lang=lang)
            return t("daily.plan.event.recurrence.daily.interval", lang=lang, interval=interval)
        
        elif "FREQ=WEEKLY" in rule_str:
            # Extract BYDAY if present
            byday = None
            if "BYDAY=" in rule_str:
                try:
                    byday_part = rule_str.split("BYDAY=")[1].split(";")[0]
                    byday = byday_part.split(",")
                except (ValueError, IndexError):
                    pass
            
            # Map day abbreviations to localized names
            day_map = {
                "MO": t("daily.plan.event.recurrence.day.monday", lang=lang),
                "TU": t("daily.plan.event.recurrence.day.tuesday", lang=lang),
                "WE": t("daily.plan.event.recurrence.day.wednesday", lang=lang),
                "TH": t("daily.plan.event.recurrence.day.thursday", lang=lang),
                "FR": t("daily.plan.event.recurrence.day.friday", lang=lang),
                "SA": t("daily.plan.event.recurrence.day.saturday", lang=lang),
                "SU": t("daily.plan.event.recurrence.day.sunday", lang=lang),
            }
            
            interval = 1
            if "INTERVAL=" in rule_str:
                try:
                    interval_part = rule_str.split("INTERVAL=")[1].split(";")[0]
                    interval = int(interval_part)
                except (ValueError, IndexError):
                    pass
            
            if byday:
                day_names = [day_map.get(day, day) for day in byday]
                if len(day_names) == 1:
                    if interval == 1:
                        return t("daily.plan.event.recurrence.weekly.day", lang=lang, day=day_names[0])
                    return t("daily.plan.event.recurrence.weekly.day.interval", lang=lang, day=day_names[0], interval=interval)
                else:
                    # Join day names with commas and "and" for the last one
                    if lang == "ru":
                        days_str = ", ".join(day_names[:-1]) + " и " + day_names[-1]
                    else:
                        days_str = ", ".join(day_names[:-1]) + " and " + day_names[-1]
                    if interval == 1:
                        return t("daily.plan.event.recurrence.weekly.days", lang=lang, days=days_str)
                    return t("daily.plan.event.recurrence.weekly.days.interval", lang=lang, days=days_str, interval=interval)
            else:
                if interval == 1:
                    return t("daily.plan.event.recurrence.weekly", lang=lang)
                return t("daily.plan.event.recurrence.weekly.interval", lang=lang, interval=interval)
        
        elif "FREQ=MONTHLY" in rule_str:
            interval = 1
            if "INTERVAL=" in rule_str:
                try:
                    interval_part = rule_str.split("INTERVAL=")[1].split(";")[0]
                    interval = int(interval_part)
                except (ValueError, IndexError):
                    pass
            
            if interval == 1:
                return t("daily.plan.event.recurrence.monthly", lang=lang)
            return t("daily.plan.event.recurrence.monthly.interval", lang=lang, interval=interval)
        
        elif "FREQ=YEARLY" in rule_str:
            interval = 1
            if "INTERVAL=" in rule_str:
                try:
                    interval_part = rule_str.split("INTERVAL=")[1].split(";")[0]
                    interval = int(interval_part)
                except (ValueError, IndexError):
                    pass
            
            if interval == 1:
                return t("daily.plan.event.recurrence.yearly", lang=lang)
            return t("daily.plan.event.recurrence.yearly.interval", lang=lang, interval=interval)
        
        # Fallback for other frequencies
        return t("daily.plan.event.recurrence.custom", lang=lang)
    
    except Exception as e:
        logger.error("Failed to parse recurrence info: %s", e)
        return t("daily.plan.event.recurrence.custom", lang=lang)


def get_event_duration(event: EventResponse, tz_info: timezone, lang: str) -> str:
    """Format event duration for display."""
    # Get the date to display (next occurrence for recurring events)
    display_date = _get_next_occurrence_date(event, tz_info)

    if event.all_day:
        date_str = display_date.astimezone(tz_info).strftime("%d.%m.%Y")
        return t("daily.plan.event.duration.all.day", lang=lang, date=date_str)

    start = display_date.astimezone(tz_info).strftime("%H:%M")
    end = (display_date + (event.date_end - event.date_start)).astimezone(tz_info).strftime("%H:%M")

    return t(
        "daily.plan.event.duration.not.all.day",
        lang=lang,
        start=start,
        end=end,
    )


async def get_event_source(event: EventResponse, store: Store, lang: str) -> str:
    calendar = await store.CalendarService.get_by_id(event.calendar_id)
    if calendar.url is not None:
        return t("daily.plan.event.source.external", lang=lang, name=calendar.name, link=calendar.url)
    return t("daily.plan.event.source.local", lang=lang)
