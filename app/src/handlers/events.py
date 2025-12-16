import os
from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from icalendar.prop import vDuration

if TYPE_CHECKING:
    pass
from dateutil.rrule import rrulestr

from i18n.strings import t
from keyboards.inline import (
    back_button,
    create_calendar,
    event_inline,
    events_create_inline,
    events_menu_inline,
    reminder_confirm_inline,
    reminder_inline,
    reminder_list_inline,
)
from logger.logger import logger
from repositories.schemas import (
    EventDurationFilter,
    EventResponse,
    ReminderCreateSchema,
    ReminderFilter,
)
from states.states import (
    EditEventStates,
    EventsMenuStates,
    ReminderManagementStates,
)
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

    # Clean all messages from previous contexts (events view, etc.)
    await clean_messages(query.bot, query.message.chat.id, state, delete_all=True)

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
        # Try to edit message, but if it fails (e.g., message was deleted), send new one
        if isinstance(query.message, Message):
            try:
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
            except Exception as e:
                # Message might be deleted, send new one instead
                logger.debug(f"Could not edit message, sending new one: {e}")
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
        context="events",
    )

    for event in events:
        is_local = await is_local_event(event, store)
        await send_message(
            query.bot,
            query.message.chat.id,
            state,
            t(
                "events.view.event.content",
                lang=lang,
                title=event.title or t("events.view.event.title.none", lang=lang),
                start_datetime=get_event_start_datetime(event, user_tz, lang),
                end_datetime=get_event_end_datetime(event, user_tz, lang),
                description=event.description or t("events.view.event.description.none", lang=lang),
                recurrence=get_event_recurrence_info(event, lang),
                source=await get_event_source(event, store, lang),
            ),
            parse_mode="HTML",
            reply_markup=event_inline(event.id, is_local, lang=lang),
            delete_keyboard=False,
            delete_message=True,
            extra_data={"event_id": event.id},
            context="events",
        )

    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        t("events.view.end", lang=lang),
        reply_markup=back_button("menu_events", lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
        delete_message=True,  # Mark for deletion when leaving events context
        context="events",
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


def get_event_start_datetime(event: EventResponse, tz_info: timezone, lang: str) -> str:
    """Format event start datetime for display.

    Args:
        event: Event to format.
        tz_info: User's timezone.
        lang: Language code.

    Returns:
        Formatted start datetime string.
    """
    display_date = _get_next_occurrence_date(event, tz_info)
    start_local = display_date.astimezone(tz_info)

    if event.all_day:
        date_str = start_local.strftime("%d.%m.%Y")
        return t("events.view.event.start.all.day", lang=lang, date=date_str)

    datetime_str = start_local.strftime("%H:%M %d.%m.%Y")
    return t("events.view.event.start.not.all.day", lang=lang, datetime=datetime_str)


def get_event_end_datetime(event: EventResponse, tz_info: timezone, lang: str) -> str:
    """Format event end datetime for display.

    Args:
        event: Event to format.
        tz_info: User's timezone.
        lang: Language code.

    Returns:
        Formatted end datetime string.
    """
    display_date = _get_next_occurrence_date(event, tz_info)
    end_date = display_date + (event.date_end - event.date_start)
    end_local = end_date.astimezone(tz_info)

    if event.all_day:
        date_str = end_local.strftime("%d.%m.%Y")
        return t("events.view.event.end.all.day", lang=lang, date=date_str)

    datetime_str = end_local.strftime("%H:%M %d.%m.%Y")
    return t("events.view.event.end.not.all.day", lang=lang, datetime=datetime_str)


async def is_local_event(event: EventResponse, store: Store) -> bool:
    """Check if event is from local calendar.

    Args:
        event: Event to check.
        store: Store instance.

    Returns:
        True if event is from local calendar, False otherwise.
    """
    calendar = await store.CalendarService.get_by_id(event.calendar_id)
    if calendar is None:
        return False
    # Local calendar has name "local calendar" and url is None
    return calendar.name == "local calendar" and calendar.url is None


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


@router.callback_query(F.data.startswith("event_delete:"))
async def event_delete(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Delete an event."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    event_id = int(query.data.split(":")[1])
    user_id = query.from_user.id

    # Get event and verify it belongs to user and is local
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        await query.answer(t("events.delete.error.not_found", lang=lang), show_alert=True)
        return

    if event.user_id != user_id:
        logger.error("Event does not belong to user", extra={"event_id": event_id, "user_id": user_id})
        await query.answer(t("events.delete.error.not_owner", lang=lang), show_alert=True)
        return

    is_local = await is_local_event(event, store)
    if not is_local:
        logger.error("Event is not local", extra={"event_id": event_id})
        await query.answer(t("events.delete.error.not_local", lang=lang), show_alert=True)
        return

    # Delete event
    await store.EventService.delete_by_id(event_id)

    # Find and delete the message with this event
    from utils.handlers import get_messages

    messages = await get_messages(state)
    message_to_delete = None
    for msg in messages:
        if msg.get("extra_data", {}) is None:
            continue
        if msg.get("extra_data", {}).get("event_id") == event_id:
            message_to_delete = msg
            break

    if message_to_delete is not None and message_to_delete.get("message_id") is not None:
        try:
            await query.bot.delete_message(chat_id=query.message.chat.id, message_id=message_to_delete["message_id"])
        except Exception as e:
            logger.warning(f"Could not delete event message: {e}")

    await query.answer(t("events.delete.success", lang=lang), show_alert=False)


def parse_reminder_time(time_str: str) -> timedelta | None:
    """Parse reminder time string to timedelta.

    Supports format HH:MM:SS (e.g., "01:30:00" for 1 hour 30 minutes).

    Args:
        time_str: Time string to parse in HH:MM:SS format.

    Returns:
        timedelta if parsing successful, None otherwise.
    """
    time_str = time_str.strip()

    # Try to parse HH:MM:SS format
    from utils.handlers import is_valid_time_hhmmss

    if is_valid_time_hhmmss(time_str):
        try:
            parts = time_str.split(":")
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2]) if len(parts) > 2 else 0
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except (ValueError, IndexError):
            pass

    return None


def format_trigger_offset(trigger_offset: str, lang: str) -> str:
    """Format trigger_offset for display in HH:MM:SS format.

    Args:
        trigger_offset: RFC 5545 trigger offset string.
        lang: Language code.

    Returns:
        Formatted string in HH:MM:SS format.
    """
    try:
        delta = vDuration.from_ical(trigger_offset)
        if isinstance(delta, timedelta):
            total_seconds = int(delta.total_seconds())
            if total_seconds < 0:
                total_seconds = abs(total_seconds)

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        pass

    return trigger_offset


@router.callback_query(F.data.startswith("event_reminders:"))
async def event_reminders(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Show reminders list for an event."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    event_id = int(query.data.split(":")[1])
    user_id = query.from_user.id

    # Get event and verify it belongs to user
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        await query.answer(t("reminders.error.event_not_found", lang=lang), show_alert=True)
        return

    if event.user_id != user_id:
        logger.error("Event does not belong to user", extra={"event_id": event_id, "user_id": user_id})
        await query.answer(t("reminders.error.not_owner", lang=lang), show_alert=True)
        return

    await clean_messages(query.bot, query.message.chat.id, state)
    await state.set_state(ReminderManagementStates.viewing_reminders)
    await state.update_data(event_id=event_id)

    # Get reminders for this event
    reminders = await store.ReminderService.find(ReminderFilter(event_id=event_id))

    # Format event info
    event_title = event.title or t("events.view.event.title.none", lang=lang)
    event_text = t("reminders.list.title", lang=lang, event_title=event_title)

    # Send main message with create button
    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        event_text,
        parse_mode="HTML",
        reply_markup=reminder_list_inline(event_id, lang=lang),
        delete_keyboard=False,
        delete_message=True,
        context="reminders",
    )

    # Send messages for each reminder
    for reminder in reminders:
        reminder_desc = reminder.description or t("reminders.description.none", lang=lang)
        reminder_time = format_trigger_offset(reminder.trigger_offset, lang)
        reminder_text = t(
            "reminders.item.content",
            lang=lang,
            description=reminder_desc,
            time=reminder_time,
        )
        await send_message(
            query.bot,
            query.message.chat.id,
            state,
            reminder_text,
            parse_mode="HTML",
            reply_markup=reminder_inline(reminder.id, event_id, lang=lang),
            delete_keyboard=False,
            delete_message=True,
            extra_data={"reminder_id": reminder.id},
            context="reminders",
        )

    # Send end message
    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        t("reminders.list.end", lang=lang),
        parse_mode="HTML",
        reply_markup=back_button("back_to_main", lang=lang),
        delete_keyboard=True,
        delete_message=True,  # Mark for deletion when leaving reminders context
        context="reminders",
    )


@router.callback_query(F.data.startswith("reminder_create:"), StateFilter(ReminderManagementStates.viewing_reminders))
async def reminder_create_start(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Start creating a new reminder."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    event_id = int(query.data.split(":")[1])
    user_id = query.from_user.id

    # Get event and verify it belongs to user
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        await query.answer(t("reminders.error.event_not_found", lang=lang), show_alert=True)
        return

    if event.user_id != user_id:
        logger.error("Event does not belong to user", extra={"event_id": event_id, "user_id": user_id})
        await query.answer(t("reminders.error.not_owner", lang=lang), show_alert=True)
        return

    # Clean messages from reminders list context before starting creation dialog
    await clean_messages(query.bot, query.message.chat.id, state, context="reminders")

    await state.set_state(ReminderManagementStates.waiting_for_reminder_description)
    await state.update_data(event_id=event_id)

    # Get event title for display
    event_title = event.title or t("events.view.event.title.none", lang=lang)

    # Send new message for creation dialog instead of editing (because list messages are deleted)
    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        t("reminders.create.enter_description", lang=lang, event_title=event_title),
        parse_mode="HTML",
        reply_markup=back_button("reminder_back", lang=lang),
        delete_keyboard=False,
        delete_message=True,  # Mark for deletion when leaving creation flow
    )


@router.message(StateFilter(ReminderManagementStates.waiting_for_reminder_description))
async def process_reminder_description(message: Message, state: FSMContext, store: Store, lang: str) -> None:
    """Process reminder description input."""
    last_message_id = await get_last_message_id(state)
    if last_message_id is None:
        logger.error("Last message id is not found", extra={"state": state})
        return

    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        logger.error("Event id is not found", extra={"state": state})
        return

    # Get event for title
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        return
    event_title = event.title or t("events.view.event.title.none", lang=lang)

    description = message.text
    await message.delete()

    if description is None or len(description) == 0:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            t("reminders.create.description.empty", lang=lang, event_title=event_title),
            parse_mode="HTML",
            reply_markup=back_button("reminder_back", lang=lang),
        )
        return

    if description == "Default reminder":
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            t("reminders.create.description.invalid", lang=lang, event_title=event_title),
            parse_mode="HTML",
            reply_markup=back_button("reminder_back", lang=lang),
        )
        return

    if len(description) > 1024:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            t("reminders.create.description.too_long", lang=lang, event_title=event_title),
            parse_mode="HTML",
            reply_markup=back_button("reminder_back", lang=lang),
        )
        return

    await state.update_data(description=description)
    await state.set_state(ReminderManagementStates.waiting_for_reminder_time)

    await edit_message(
        message.bot,
        message.chat.id,
        last_message_id,
        state,
        t("reminders.create.enter_time", lang=lang, event_title=event_title),
        parse_mode="HTML",
        reply_markup=back_button("reminder_back", lang=lang),
    )


@router.message(StateFilter(ReminderManagementStates.waiting_for_reminder_time))
async def process_reminder_time(message: Message, state: FSMContext, store: Store, lang: str) -> None:
    """Process reminder time input."""
    last_message_id = await get_last_message_id(state)
    if last_message_id is None:
        logger.error("Last message id is not found", extra={"state": state})
        return

    data = await state.get_data()
    event_id = data.get("event_id")
    description = data.get("description")
    if event_id is None or description is None:
        logger.error("Event id or description is not found", extra={"state": state})
        return

    # Get event for title
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        return
    event_title = event.title or t("events.view.event.title.none", lang=lang)

    time_str = message.text
    await message.delete()

    if time_str is None or len(time_str) == 0:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            t("reminders.create.time.empty", lang=lang, event_title=event_title),
            parse_mode="HTML",
            reply_markup=back_button("reminder_back", lang=lang),
        )
        return

    # Parse time string to timedelta
    delta = parse_reminder_time(time_str)
    if delta is None:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            t("reminders.create.time.invalid", lang=lang, event_title=event_title),
            parse_mode="HTML",
            reply_markup=back_button("reminder_back", lang=lang),
        )
        return

    # Convert timedelta to trigger_offset
    trigger_offset = vDuration(delta).to_ical().decode("utf-8")
    # Make it negative (before event)
    if not trigger_offset.startswith("-"):
        trigger_offset = "-" + trigger_offset

    await state.update_data(trigger_offset=trigger_offset)
    await state.set_state(ReminderManagementStates.waiting_for_reminder_confirmation)

    # Get event to show preview
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        return

    event_title = event.title or t("events.view.event.title.none", lang=lang)
    formatted_time = format_trigger_offset(trigger_offset, lang)

    await edit_message(
        message.bot,
        message.chat.id,
        last_message_id,
        state,
        t(
            "reminders.create.confirm",
            lang=lang,
            event_title=event_title,
            description=description,
            time=formatted_time,
        ),
        parse_mode="HTML",
        reply_markup=reminder_confirm_inline(lang=lang),
    )


@router.callback_query(
    F.data == "reminder_confirm", StateFilter(ReminderManagementStates.waiting_for_reminder_confirmation)
)
async def reminder_confirm(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Confirm reminder creation."""
    data = await state.get_data()
    event_id = data.get("event_id")
    description = data.get("description")
    trigger_offset = data.get("trigger_offset")

    if event_id is None or description is None or trigger_offset is None:
        logger.error("Required data is not found", extra={"state": state})
        await query.answer(t("reminders.create.error.missing_data", lang=lang), show_alert=True)
        return

    # Create reminder
    try:
        await store.ReminderService.create(
            ReminderCreateSchema(
                event_id=event_id,
                description=description,
                trigger_offset=trigger_offset,
            )
        )
    except Exception as e:
        logger.error(f"Error creating reminder: {e}", exc_info=e)
        await query.answer(t("reminders.create.error.failed", lang=lang), show_alert=True)
        return

    await query.answer(t("reminders.create.success", lang=lang), show_alert=False)

    # Clean all messages and return to main menu after successful creation
    if query.bot is None or query.message is None:
        logger.error("Query bot or message is None", extra={"query": query})
        return

    await clean_messages(query.bot, query.message.chat.id, state, delete_all=True)

    # Return to main menu
    from handlers.start import back_to_main

    await back_to_main(
        type(
            "Query",
            (),
            {
                "data": "back_to_main",
                "from_user": query.from_user,
                "bot": query.bot,
                "message": query.message,
            },
        )(),
        state,
        lang,
    )


@router.callback_query(F.data.startswith("reminder_delete:"))
async def reminder_delete(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Delete a reminder."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    reminder_id = int(query.data.split(":")[1])
    user_id = query.from_user.id

    # Get reminder and verify it belongs to user's event
    reminder = await store.ReminderService.get_by_id(reminder_id)
    if reminder is None:
        logger.error("Reminder is not found", extra={"reminder_id": reminder_id})
        await query.answer(t("reminders.delete.error.not_found", lang=lang), show_alert=True)
        return

    event = await store.EventService.get_by_id(reminder.event_id)
    if event is None or event.user_id != user_id:
        logger.error("Event does not belong to user", extra={"reminder_id": reminder_id, "user_id": user_id})
        await query.answer(t("reminders.delete.error.not_owner", lang=lang), show_alert=True)
        return

    # Delete reminder
    await store.ReminderService.delete_by_id(reminder_id)

    # Find and delete the message with this reminder
    from utils.handlers import get_messages

    messages = await get_messages(state)
    message_to_delete = None
    for msg in messages:
        if msg.get("extra_data", {}) is None:
            continue
        if msg.get("extra_data", {}).get("reminder_id") == reminder_id:
            message_to_delete = msg
            break

    if message_to_delete is not None and message_to_delete.get("message_id") is not None:
        try:
            await query.bot.delete_message(chat_id=query.message.chat.id, message_id=message_to_delete["message_id"])
        except Exception as e:
            logger.warning(f"Could not delete reminder message: {e}")

    await query.answer(t("reminders.delete.success", lang=lang), show_alert=False)


@router.callback_query(F.data.startswith("reminder_back"))
async def reminder_back(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Go back from reminder creation to main menu."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    if query.bot is None or query.message is None:
        logger.error("Query bot or message is None", extra={"query": query})
        return

    current_state = await state.get_state()

    # If in reminder creation flow, cancel and return to main menu
    if current_state in [
        ReminderManagementStates.waiting_for_reminder_description,
        ReminderManagementStates.waiting_for_reminder_time,
        ReminderManagementStates.waiting_for_reminder_confirmation,
    ]:
        # Clean all messages and return to main menu
        await clean_messages(query.bot, query.message.chat.id, state, delete_all=True)

        # Send main menu message
        from handlers.start import back_to_main

        await back_to_main(
            type(
                "Query",
                (),
                {
                    "data": "back_to_main",
                    "from_user": query.from_user,
                    "bot": query.bot,
                    "message": query.message,
                },
            )(),
            state,
            lang,
        )
    else:
        # Return to main menu (from reminders list end message)
        if query.bot is None or query.message is None:
            logger.error("Query bot or message is None", extra={"query": query})
            return
        await clean_messages(query.bot, query.message.chat.id, state, delete_all=True)
        from handlers.start import back_to_main

        await back_to_main(
            type(
                "Query",
                (),
                {
                    "data": "back_to_main",
                    "from_user": query.from_user,
                    "bot": query.bot,
                    "message": query.message,
                },
            )(),
            state,
            lang,
        )


@router.callback_query(F.data.startswith("event_edit:"))
async def event_edit_start(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Start editing an event."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    event_id = int(query.data.split(":")[1])
    user_id = query.from_user.id

    # Get event and verify it belongs to user and is local
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        await query.answer(t("events.edit.error.not_found", lang=lang), show_alert=True)
        return

    if event.user_id != user_id:
        logger.error("Event does not belong to user", extra={"event_id": event_id, "user_id": user_id})
        await query.answer(t("events.edit.error.not_owner", lang=lang), show_alert=True)
        return

    is_local = await is_local_event(event, store)
    if not is_local:
        logger.error("Event is not local", extra={"event_id": event_id})
        await query.answer(t("events.edit.error.not_local", lang=lang), show_alert=True)
        return

    # Clean messages from event view context before starting edit dialog
    if query.bot is None or query.message is None:
        logger.error("Query bot or message is None", extra={"query": query})
        return

    await clean_messages(query.bot, query.message.chat.id, state, delete_all=True)

    # Get user settings for timezone
    from datetime import UTC

    settings_data = await store.SettingsService.get_by_user_id(user_id)
    if settings_data and settings_data.timezone:
        user_tz = parse_user_timezone(settings_data.timezone)
    else:
        user_tz = UTC

    # Store original event data
    original_start_str = event.date_start.astimezone(user_tz).strftime("%d.%m.%Y") if event.date_start else None
    original_start_time_str = (
        event.date_start.astimezone(user_tz).strftime("%H:%M") if event.date_start and not event.all_day else None
    )
    original_end_str = event.date_end.astimezone(user_tz).strftime("%d.%m.%Y") if event.date_end else None
    original_end_time_str = (
        event.date_end.astimezone(user_tz).strftime("%H:%M") if event.date_end and not event.all_day else None
    )

    await state.update_data(
        event_id=event_id,
        original_title=event.title,
        original_description=event.description,
        original_start_date=original_start_str,
        original_start_time=original_start_time_str,
        original_end_date=original_end_str,
        original_end_time=original_end_time_str,
        original_date_start=event.date_start.isoformat() if event.date_start else None,
        original_date_end=event.date_end.isoformat() if event.date_end else None,
        original_all_day=event.all_day,
    )

    # Start sequential edit dialog - begin with title
    await state.set_state(EditEventStates.waiting_for_new_title)
    from keyboards.inline import skip_inline
    from utils.handlers import send_message

    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        f"{t('events.edit.enter_title', lang=lang)}\n\n<i>{t('events.edit.skip_hint', lang=lang)}</i>",
        skip_inline("edit_event_skip_title", "edit_event_cancel", lang=lang),
        parse_mode="HTML",
        delete_keyboard=False,
        delete_message=True,
    )
