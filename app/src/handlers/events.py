import os
from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

if TYPE_CHECKING:
    pass
from dateutil.rrule import rrulestr

from i18n.strings import t
from keyboards.inline import (
    back_button,
    create_calendar,
    events_create_inline,
    events_menu_inline,
)
from logger.logger import logger
from repositories.schemas import EventDurationFilter, EventResponse
from states.states import EventsMenuStates
from store.store import Store
from utils.handlers import clean_messages, edit_message, get_last_message_id, parse_user_timezone, send_message

router = Router()


@router.callback_query(F.data == "menu_events")
async def open_events_menu(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open events menu."""

    await state.set_state(EventsMenuStates.in_events_menu)

    if query.bot is None or query.message is None:
        logger.error("Query bot or message is None", extra={"query": query})
        return

    await clean_messages(query.bot, query.message.chat.id, state)

    # Check if message contains a document (file) - cannot edit such messages
    # Need to check if message is a Message instance (not InaccessibleMessage)
    if isinstance(query.message, Message) and query.message.document is not None:
        # Delete message with file and send new text message
        try:
            await query.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
        except Exception as e:
            logger.warning(f"Could not delete message with file: {e}")

        await send_message(
            query.bot,
            query.message.chat.id,
            state,
            t("events.title", lang=lang),
            reply_markup=events_menu_inline(lang=lang),
            parse_mode="HTML",
            delete_keyboard=True,
            delete_message=False,
        )
    else:
        # Regular text message - can be edited
        if isinstance(query.message, Message):
            await edit_message(
                query.bot,
                query.message.chat.id,
                query.message.message_id,
                state,
                t("events.title", lang=lang),
                events_menu_inline(lang=lang),
                parse_mode="HTML",
                delete_keyboard=True,
                delete_message=False,
            )
        else:
            # Fallback if message is not accessible
            await send_message(
                query.bot,
                query.message.chat.id,
                state,
                t("events.title", lang=lang),
                reply_markup=events_menu_inline(lang=lang),
                parse_mode="HTML",
                delete_keyboard=True,
                delete_message=False,
            )


@router.callback_query(F.data == "events_import", StateFilter(EventsMenuStates.in_events_menu))
async def events_import(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Open import feature - request .ics file from user."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is importing events")

    await state.set_state(EventsMenuStates.in_events_import)
    await query.answer(t("events.import.selected", lang=lang))

    text = f"{t('events.import.title', lang=lang)}\n\n{t('events.import.description', lang=lang)}"
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=text,
        reply_markup=back_button("menu_events", lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
        delete_message=False,
    )


@router.callback_query(F.data == "events_export", StateFilter(EventsMenuStates.in_events_menu))
async def events_export(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Export local calendar events to .ics file."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is exporting events")

    await query.answer(t("events.export.selected", lang=lang))

    if query.bot is None or query.message is None:
        logger.error("Query bot or message is None", extra={"query": query})
        return

    try:
        # Generate .ics file
        file_path = await store.ExportService.export_local_calendar_to_file(user_id)

        # Delete old message before sending file
        try:
            await query.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
        except Exception as e:
            logger.warning(f"Could not delete old message: {e}")

        # Send file to user with caption
        document = FSInputFile(file_path, filename="calendar.ics")
        await query.bot.send_document(
            chat_id=query.message.chat.id,
            document=document,
            caption=f"{t('events.export.title', lang=lang)}\n\n{t('events_export_success', lang=lang)}",
            reply_markup=back_button("menu_events", lang=lang),
            parse_mode="HTML",
        )

        # Clean up temporary file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting temporary file {file_path}: {e}", exc_info=e)

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            error_text = t("events_export_error_no_calendar", lang=lang)
        elif "no events" in error_msg.lower():
            error_text = t("events_export_error_no_events", lang=lang)
        else:
            error_text = t("events_export_error", lang=lang)

        logger.error(f"Error exporting calendar for user {user_id}: {e}", exc_info=e)
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            text=f"{t('events.export.title', lang=lang)}\n\n{error_text}",
            reply_markup=back_button("menu_events", lang=lang),
            parse_mode="HTML",
            delete_keyboard=True,
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting calendar for user {user_id}: {e}", exc_info=e)
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            text=f"{t('events.export.title', lang=lang)}\n\n{t('events_export_error', lang=lang)}",
            reply_markup=back_button("menu_events", lang=lang),
            parse_mode="HTML",
            delete_keyboard=True,
        )


@router.callback_query(F.data == "events_create", StateFilter(EventsMenuStates.in_events_menu))
async def events_create(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open event creation feature"""
    user_id = query.from_user.id
    logger.info(f"User {user_id} is choosing creating event option")

    await state.set_state(EventsMenuStates.in_events_create)
    await query.answer(t("events.create.selected", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
        text = f"{t('events.create.title', lang=lang)}\n\n<i>{t('events.feature_dev', lang=lang)}</i>"
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=events_create_inline(lang=lang),
        )


@router.callback_query(F.data == "events_view", StateFilter(EventsMenuStates.in_events_menu))
async def events_view(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open event view feature with calendar for date range selection."""

    await state.set_state(EventsMenuStates.selecting_date_range)
    await query.answer(t("events.view.selected", lang=lang))

    # Initialize state with current year and month
    now = datetime.now()
    await state.update_data(calendar_year=now.year, calendar_month=now.month, start_date=None, end_date=None)

    text = f"{t('events.view.title', lang=lang)}\n\n{t('events.view.select.start.date', lang=lang)}"
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=text,
        reply_markup=create_calendar(year=now.year, month=now.month, lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
        delete_message=False,
    )


@router.callback_query(F.data == "prev_month", StateFilter(EventsMenuStates.selecting_date_range))
async def prev_month(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Navigate to previous month in calendar."""
    data = await state.get_data()
    year = data.get("calendar_year", datetime.now().year)
    month = data.get("calendar_month", datetime.now().month)
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    # Decrease month
    month -= 1
    if month < 1:
        month = 12
        year -= 1

    await state.update_data(calendar_year=year, calendar_month=month)

    # Convert start_date and end_date from string to datetime if they exist
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
    if end_date:
        end_dt = datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date

    text = f"{t('events.view.title', lang=lang)}\n\n"
    if start_dt and end_dt:
        text += t("events.view.select.complete", lang=lang)
    elif start_dt:
        text += t("events.view.select.end.date", lang=lang)
    else:
        text += t("events.view.select.start.date", lang=lang)

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=text,
        reply_markup=create_calendar(year=year, month=month, lang=lang, start_date=start_dt, end_date=end_dt),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "next_month", StateFilter(EventsMenuStates.selecting_date_range))
async def next_month(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Navigate to next month in calendar."""
    data = await state.get_data()
    year = data.get("calendar_year", datetime.now().year)
    month = data.get("calendar_month", datetime.now().month)
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    # Increase month
    month += 1
    if month > 12:
        month = 1
        year += 1

    await state.update_data(calendar_year=year, calendar_month=month)

    # Convert start_date and end_date from string to datetime if they exist
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
    if end_date:
        end_dt = datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date

    text = f"{t('events.view.title', lang=lang)}\n\n"
    if start_dt and end_dt:
        text += t("events.view.select.complete", lang=lang)
    elif start_dt:
        text += t("events.view.select.end.date", lang=lang)
    else:
        text += t("events.view.select.start.date", lang=lang)

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=text,
        reply_markup=create_calendar(year=year, month=month, lang=lang, start_date=start_dt, end_date=end_dt),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("day_"), StateFilter(EventsMenuStates.selecting_date_range))
async def select_date(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Handle date selection in calendar."""
    if query.data is None:
        return

    day = int(query.data.split("_")[1])
    data = await state.get_data()
    year = data.get("calendar_year", datetime.now().year)
    month = data.get("calendar_month", datetime.now().month)
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    # Convert start_date from string to datetime if it exists
    start_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date

    # Create naive datetime (date only, no time)
    selected_date = datetime(year, month, day)

    # If start_date is not selected, select it
    if start_dt is None:
        await state.update_data(start_date=selected_date.isoformat())
        start_dt = selected_date
        text = f"{t('events.view.title', lang=lang)}\n\n{t('events.view.select.end.date', lang=lang)}"
    # If start_date is selected but end_date is not, select end_date
    elif end_date is None:
        # Check if selected date is after start_date
        if selected_date.date() < start_dt.date():
            await query.answer(t("events.view.date.before.start", lang=lang), show_alert=True)
            return

        await state.update_data(end_date=selected_date.isoformat())
        end_dt = selected_date

        # Both dates selected, show events
        await show_events_in_range(query, state, store, lang, start_dt, end_dt)
        return
    else:
        # Both dates already selected, reset and start over
        await state.update_data(start_date=selected_date.isoformat(), end_date=None)
        start_dt = selected_date
        text = f"{t('events.view.title', lang=lang)}\n\n{t('events.view.select.end.date', lang=lang)}"

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=text,
        reply_markup=create_calendar(year=year, month=month, lang=lang, start_date=start_dt, end_date=None),
        parse_mode="HTML",
    )


async def show_events_in_range(
    query: CallbackQuery, state: FSMContext, store: Store, lang: str, start_date: datetime, end_date: datetime
) -> None:
    """Display events in the selected date range."""
    user_id = query.from_user.id

    settings = await store.SettingsService.get_by_user_id(user_id)
    user_tz = parse_user_timezone(settings.timezone)

    # Convert local dates to UTC for querying
    # Set time to start of day for start_date and end of day for end_date
    # Dates are naive (date only), so we create them in user timezone
    start_local = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, 0, tzinfo=user_tz)
    end_local = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999, tzinfo=user_tz)

    utc_from = start_local.astimezone(UTC)
    utc_to = end_local.astimezone(UTC)

    events = await store.EventService.get_events_in_range(
        EventDurationFilter(user_id=user_id, duration_from=utc_from, duration_to=utc_to)
    )

    # Clear state
    await state.update_data(start_date=None, end_date=None)
    await state.set_state(EventsMenuStates.in_events_view)

    # Format date range for display
    start_str = start_date.strftime("%d.%m.%Y")
    end_str = end_date.strftime("%d.%m.%Y")

    if events == []:
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            text=(
                f"{t('events.view.title', lang=lang)}\n\n"
                f"{t('events.view.range', lang=lang, start=start_str, end=end_str)}\n\n"
                f"{t('events.view.no.events', lang=lang)}"
            ),
            reply_markup=back_button("menu_events", lang=lang),
            parse_mode="HTML",
            delete_keyboard=True,
        )
        return

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=(
            f"{t('events.view.title', lang=lang)}\n\n{t('events.view.range', lang=lang, start=start_str, end=end_str)}"
        ),
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
                "events.view.event.content",
                lang=lang,
                title=event.title or t("events.view.event.title.none", lang=lang),
                description=event.description or t("events.view.event.description.none", lang=lang),
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
        t("events.view.end", lang=lang),
        reply_markup=back_button("menu_events", lang=lang),
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
            return t("events.view.event.recurrence.rdate.single", lang=lang)
        return t("events.view.event.recurrence.rdate.multiple", lang=lang, count=str(count))

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
                return t("events.view.event.recurrence.daily", lang=lang)
            return t("events.view.event.recurrence.daily.interval", lang=lang, interval=str(interval))

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
                "MO": t("events.view.event.recurrence.day.monday", lang=lang),
                "TU": t("events.view.event.recurrence.day.tuesday", lang=lang),
                "WE": t("events.view.event.recurrence.day.wednesday", lang=lang),
                "TH": t("events.view.event.recurrence.day.thursday", lang=lang),
                "FR": t("events.view.event.recurrence.day.friday", lang=lang),
                "SA": t("events.view.event.recurrence.day.saturday", lang=lang),
                "SU": t("events.view.event.recurrence.day.sunday", lang=lang),
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
                        return t("events.view.event.recurrence.weekly.day", lang=lang, day=day_names[0])
                    return t(
                        "events.view.event.recurrence.weekly.day.interval",
                        lang=lang,
                        day=day_names[0],
                        interval=str(interval),
                    )
                else:
                    # Join day names with commas and "and" for the last one
                    if lang == "ru":
                        days_str = ", ".join(day_names[:-1]) + " и " + day_names[-1]
                    else:
                        days_str = ", ".join(day_names[:-1]) + " and " + day_names[-1]
                    if interval == 1:
                        return t("events.view.event.recurrence.weekly.days", lang=lang, days=days_str)
                    return t(
                        "events.view.event.recurrence.weekly.days.interval",
                        lang=lang,
                        days=days_str,
                        interval=str(interval),
                    )
            else:
                if interval == 1:
                    return t("events.view.event.recurrence.weekly", lang=lang)
                return t("events.view.event.recurrence.weekly.interval", lang=lang, interval=str(interval))

        elif "FREQ=MONTHLY" in rule_str:
            interval = 1
            if "INTERVAL=" in rule_str:
                try:
                    interval_part = rule_str.split("INTERVAL=")[1].split(";")[0]
                    interval = int(interval_part)
                except (ValueError, IndexError):
                    pass

            if interval == 1:
                return t("events.view.event.recurrence.monthly", lang=lang)
            return t("events.view.event.recurrence.monthly.interval", lang=lang, interval=str(interval))

        elif "FREQ=YEARLY" in rule_str:
            interval = 1
            if "INTERVAL=" in rule_str:
                try:
                    interval_part = rule_str.split("INTERVAL=")[1].split(";")[0]
                    interval = int(interval_part)
                except (ValueError, IndexError):
                    pass

            if interval == 1:
                return t("events.view.event.recurrence.yearly", lang=lang)
            return t("events.view.event.recurrence.yearly.interval", lang=lang, interval=str(interval))

        # Fallback for other frequencies
        return t("events.view.event.recurrence.custom", lang=lang)

    except Exception as e:
        logger.error("Failed to parse recurrence info: %s", e)
        return t("events.view.event.recurrence.custom", lang=lang)


def get_event_duration(event: EventResponse, tz_info: timezone, lang: str) -> str:
    """Format event duration for display."""
    # Get the date to display (next occurrence for recurring events)
    display_date = _get_next_occurrence_date(event, tz_info)

    if event.all_day:
        date_str = display_date.astimezone(tz_info).strftime("%d.%m.%Y")
        return t("events.view.event.duration.all.day", lang=lang, date=date_str)

    start = display_date.astimezone(tz_info).strftime("%H:%M")
    end = (display_date + (event.date_end - event.date_start)).astimezone(tz_info).strftime("%H:%M")
    date_str = display_date.astimezone(tz_info).strftime("%d.%m.%Y")

    return t("events.view.event.duration.not.all.day", lang=lang, date=date_str, start=start, end=end)


async def get_event_source(event: EventResponse, store: Store, lang: str) -> str:
    """Get event source (external calendar or local)."""
    calendar = await store.CalendarService.get_by_id(event.calendar_id)
    if calendar is None:
        return t("events.view.event.source.local", lang=lang)
    if calendar.url is not None:
        return t("events.view.event.source.external", lang=lang, name=calendar.name, link=calendar.url)
    return t("events.view.event.source.local", lang=lang)


@router.callback_query(F.data == "ignore", StateFilter(EventsMenuStates.selecting_date_range))
async def ignore_callback(query: CallbackQuery) -> None:
    """Ignore callback for calendar header buttons."""
    await query.answer()


@router.message(StateFilter(EventsMenuStates.in_events_import))
async def process_ics_file(message: Message, state: FSMContext, store: Store, lang: str) -> None:
    """Process uploaded .ics file."""
    if message.from_user is None:
        logger.error("Message from_user is None", extra={"message": message})
        return

    user_id = message.from_user.id

    if message.bot is None:
        logger.error("Message bot is None", extra={"message": message})
        return

    # Delete user message with file
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Could not delete user message: {e}")

    # Get last message ID to edit it
    last_message_id = await get_last_message_id(state)

    # Check if message has document
    if message.document is None:
        if last_message_id is not None:
            await edit_message(
                message.bot,
                message.chat.id,
                last_message_id,
                state,
                f"{t('events.import.title', lang=lang)}\n\n{t('events_import_error_no_file', lang=lang)}",
                reply_markup=back_button("menu_events", lang=lang),
                parse_mode="HTML",
            )
        else:
            await message.answer(t("events_import_error_no_file", lang=lang), parse_mode="HTML")
        return

    # Check if file is .ics
    file_name = message.document.file_name
    if file_name is None or not file_name.endswith(".ics"):
        if last_message_id is not None:
            await edit_message(
                message.bot,
                message.chat.id,
                last_message_id,
                state,
                f"{t('events.import.title', lang=lang)}\n\n{t('events_import_error_invalid_format', lang=lang)}",
                reply_markup=back_button("menu_events", lang=lang),
                parse_mode="HTML",
            )
        else:
            await message.answer(t("events_import_error_invalid_format", lang=lang), parse_mode="HTML")
        return

    try:
        # Import file using UploadService
        await store.UploadService.upload_ics_file(message, message.bot)

        # Edit last message with success text
        if last_message_id is not None:
            await edit_message(
                message.bot,
                message.chat.id,
                last_message_id,
                state,
                f"{t('events.import.title', lang=lang)}\n\n{t('events_import_success', lang=lang)}",
                reply_markup=back_button("menu_events", lang=lang),
                parse_mode="HTML",
            )
        else:
            await message.answer(t("events_import_success", lang=lang), parse_mode="HTML")

        # Return to events menu
        await state.set_state(EventsMenuStates.in_events_menu)

    except ValueError as e:
        error_msg = str(e)
        if "must be .ics" in error_msg.lower():
            error_text = t("events_import_error_invalid_format", lang=lang)
        else:
            error_text = t("events_import_error", lang=lang)
        logger.error(f"Error importing calendar for user {user_id}: {e}", exc_info=e)
        if last_message_id is not None:
            await edit_message(
                message.bot,
                message.chat.id,
                last_message_id,
                state,
                f"{t('events.import.title', lang=lang)}\n\n{error_text}",
                reply_markup=back_button("menu_events", lang=lang),
                parse_mode="HTML",
            )
        else:
            await message.answer(error_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Unexpected error importing calendar for user {user_id}: {e}", exc_info=e)
        if last_message_id is not None:
            await edit_message(
                message.bot,
                message.chat.id,
                last_message_id,
                state,
                f"{t('events.import.title', lang=lang)}\n\n{t('events_import_error', lang=lang)}",
                reply_markup=back_button("menu_events", lang=lang),
                parse_mode="HTML",
            )
        else:
            await message.answer(t("events_import_error", lang=lang), parse_mode="HTML")
