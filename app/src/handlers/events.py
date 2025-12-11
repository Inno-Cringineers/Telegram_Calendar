import os
from datetime import UTC, datetime, timezone

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

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
from utils.handlers import clean_messages, edit_message, parse_user_timezone, send_message

router = Router()


@router.callback_query(F.data == "menu_events")
async def open_events_menu(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Open events menu."""

    await state.set_state(EventsMenuStates.in_events_menu)

    await clean_messages(query.bot, query.message.chat.id, state)

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

        # Send file to user
        document = FSInputFile(file_path, filename="calendar.ics")
        await query.bot.send_document(
            chat_id=query.message.chat.id,
            document=document,
            caption=t("events_export_success", lang=lang),
        )

        # Clean up temporary file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error deleting temporary file {file_path}: {e}", exc_info=e)

        # Update message
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            text=f"{t('events.export.title', lang=lang)}\n\n{t('events_export_success', lang=lang)}",
            reply_markup=back_button("menu_events", lang=lang),
            parse_mode="HTML",
            delete_keyboard=True,
        )

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


def get_event_duration(event: EventResponse, tz_info: timezone, lang: str) -> str:
    """Format event duration for display."""
    if event.all_day:
        return t("events.view.event.duration.all.day", lang=lang)

    start = event.date_start.astimezone(tz_info).strftime("%H:%M")
    end = event.date_end.astimezone(tz_info).strftime("%H:%M")
    date_str = event.date_start.astimezone(tz_info).strftime("%d.%m.%Y")

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

    # Check if message has document
    if message.document is None:
        await message.answer(t("events_import_error_no_file", lang=lang), parse_mode="HTML")
        return

    # Check if file is .ics
    file_name = message.document.file_name
    if file_name is None or not file_name.endswith(".ics"):
        await message.answer(t("events_import_error_invalid_format", lang=lang), parse_mode="HTML")
        return

    try:
        # Import file using UploadService
        await store.UploadService.upload_ics_file(message, message.bot)
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
        await message.answer(error_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Unexpected error importing calendar for user {user_id}: {e}", exc_info=e)
        await message.answer(t("events_import_error", lang=lang), parse_mode="HTML")
