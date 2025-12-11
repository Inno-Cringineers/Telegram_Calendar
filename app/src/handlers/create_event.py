"""Handlers for creating events through dialog."""

import uuid
from datetime import UTC, datetime, timedelta

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import back_button, cancel_inline, event_confirmation_inline, skip_inline, start_time_inline
from logger.logger import logger
from middlewares.settings_middleware import SettingsData
from repositories.schemas import CalendarCreateSchema, EventCreateSchema
from states.states import CreateEventStates, EventsMenuStates
from store.store import Store
from utils.handlers import edit_message, get_last_message_id, is_valid_time_hhmm, parse_user_timezone

router = Router()


def is_valid_date(date_str: str) -> bool:
    """Validate date format DD.MM.YYYY.

    Args:
        date_str: Date string to validate.

    Returns:
        True if valid, False otherwise.
    """
    try:
        event_date = datetime.strptime(date_str, "%d.%m.%Y")
        # Check if date is not in the past
        if event_date.date() < datetime.now().date():
            return False
        return True
    except ValueError:
        return False


@router.callback_query(F.data == "create_new_event", StateFilter(EventsMenuStates.in_events_create))
async def process_create_new_event_callback(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Start event creation dialog."""

    await state.set_state(CreateEventStates.waiting_for_title)

    text = f"{t('create_event.enter_title', lang=settings.lang)}\n\n"
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        cancel_inline("events_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "events_cancel", StateFilter(CreateEventStates))
async def cancel_event_creation(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Cancel event creation."""
    await state.clear()
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        t("create_event.cancelled", lang=settings.lang),
        back_button("menu_events", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(CreateEventStates.waiting_for_title))
async def process_event_title(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process event title."""
    title = message.text

    # Delete user message
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if title is None:
        title = "nothing" if settings.lang == "en" else "ничего"

    text = (
        f"{t('create_event.enter_title', lang=settings.lang)}\n\n"
        f"<i>{t('create_event.title_empty', lang=settings.lang)}</i>"
    )
    if title is None or len(title) == 0:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            cancel_inline("events_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    text = (
        f"{t('create_event.enter_title', lang=settings.lang)}\n\n"
        f"<i>{t('create_event.title_too_long', lang=settings.lang)}</i>"
    )
    if len(title) > 100:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            cancel_inline("events_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(title=title)
    await state.set_state(CreateEventStates.waiting_for_description)

    text = f"{t('create_event.enter_description', lang=settings.lang)}\n\n"
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        skip_inline(skip_callback="skip_description", cancel_callback="events_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(CreateEventStates.waiting_for_description))
async def process_event_description(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process event description."""
    description = message.text

    # Delete user message
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    await state.update_data(description=description)
    await state.set_state(CreateEventStates.waiting_for_start_date)

    text = t("create_event.enter_date", lang=settings.lang)
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        cancel_inline("events_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "skip_description", StateFilter(CreateEventStates.waiting_for_description))
async def skip_event_description(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Skip event description step."""
    await state.update_data(description=None)
    await state.set_state(CreateEventStates.waiting_for_start_date)

    text = t("create_event.enter_date", lang=settings.lang)
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        cancel_inline("events_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(CreateEventStates.waiting_for_start_date))
async def process_event_date(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process event date with validation."""
    date_str = message.text

    # Delete user message
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if date_str is None:
        date_str = "nothing" if settings.lang == "en" else "ничего"

    if date_str is None or not is_valid_date(date_str.strip()):
        text = (
            f"{t('create_event.enter_date', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.date_format_error', lang=settings.lang, user_input=date_str)}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            cancel_inline("events_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(start_date=date_str.strip())
    await state.set_state(CreateEventStates.waiting_for_start_time)

    text = t("create_event.enter_time", lang=settings.lang)
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        start_time_inline("events_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "event_all_day", StateFilter(CreateEventStates.waiting_for_start_time))
async def process_event_all_day(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Process all day event selection."""
    await state.update_data(all_day=True, start_time=None, end_time=None)
    await state.set_state(CreateEventStates.waiting_for_confirmation)

    # Show preview of the event
    data = await state.get_data()
    description_text = (
        data.get("description")
        if data.get("description")
        else t("create_event.preview.description_none", lang=settings.lang)
    )
    preview_text = (
        f"{t('create_event.preview.title', lang=settings.lang)}\n\n"
        f"{t('create_event.preview.title_label', lang=settings.lang, title=data['title'])}\n"
        f"{t('create_event.preview.description_label', lang=settings.lang, description=description_text)}\n"
        f"{t('create_event.preview.date_label', lang=settings.lang, date=data['start_date'])}\n"
        f"{t('create_event.preview.all_day_label', lang=settings.lang)}\n\n"
        f"<i>{t('create_event.preview.confirm', lang=settings.lang)}</i>"
    )

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        preview_text,
        event_confirmation_inline(lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(CreateEventStates.waiting_for_start_time))
async def process_event_time(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process event time with validation."""
    time_str = message.text

    # Delete user message
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if time_str is None:
        time_str = "nothing" if settings.lang == "en" else "ничего"

    if time_str is None or not is_valid_time_hhmm(time_str.strip()):
        text = (
            f"{t('create_event.enter_time', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.time_format_error', lang=settings.lang, user_input=time_str)}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            start_time_inline("events_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(start_time=time_str.strip())
    await state.set_state(CreateEventStates.waiting_for_end_time)

    text = t("create_event.enter_end_time", lang=settings.lang)
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        cancel_inline("events_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(CreateEventStates.waiting_for_end_time))
async def process_event_end_time(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process event end time with validation."""
    time_str = message.text

    # Delete user message
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if time_str is None:
        time_str = "nothing" if settings.lang == "en" else "ничего"

    if time_str is None or not is_valid_time_hhmm(time_str.strip()):
        text = (
            f"{t('create_event.enter_end_time', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.time_format_error', lang=settings.lang, user_input=time_str)}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            cancel_inline("events_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(end_time=time_str.strip())
    await state.set_state(CreateEventStates.waiting_for_confirmation)

    # Show preview of the event
    data = await state.get_data()
    description_text = (
        data.get("description")
        if data.get("description")
        else t("create_event.preview.description_none", lang=settings.lang)
    )
    preview_text = (
        f"{t('create_event.preview.title', lang=settings.lang)}\n\n"
        f"{t('create_event.preview.title_label', lang=settings.lang, title=data['title'])}\n"
        f"{t('create_event.preview.description_label', lang=settings.lang, description=description_text)}\n"
        f"{t('create_event.preview.date_label', lang=settings.lang, date=data['start_date'])}\n"
        f"{t('create_event.preview.time_label', lang=settings.lang, time=data['start_time'])}\n"
        f"{t('create_event.preview.end_time_label', lang=settings.lang, time=time_str.strip())}\n\n"
        f"<i>{t('create_event.preview.confirm', lang=settings.lang)}</i>"
    )

    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        preview_text,
        event_confirmation_inline(lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "confirm_event", StateFilter(CreateEventStates.waiting_for_confirmation))
async def confirm_event(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Confirm and save event."""
    data = await state.get_data()
    user_id = query.from_user.id

    all_day = data.get("all_day", False)
    logger.info(
        f"User {user_id} confirmed event creation: "
        f"title={data['title']}, date={data['start_date']}, "
        f"all_day={all_day}, start_time={data.get('start_time')}, end_time={data.get('end_time')}"
    )

    try:
        # Get or create local calendar
        calendars = await store.CalendarService.get_by_user_id(user_id)
        local_calendar = None
        for calendar in calendars:
            if calendar.name == "local calendar":
                local_calendar = calendar
                break

        if local_calendar is None:
            local_calendar = await store.CalendarService.create(
                CalendarCreateSchema(user_id=user_id, name="local calendar", url=None)
            )

        user_tz = parse_user_timezone(settings.timezone)
        date_obj = datetime.strptime(data["start_date"], "%d.%m.%Y")

        if all_day:
            # For all day events, start at 00:00:00 and end at 23:59:59 of the same day
            local_datetime_start = datetime.combine(date_obj.date(), datetime.min.time()).replace(tzinfo=user_tz)
            max_time = datetime.max.time().replace(microsecond=0)
            local_datetime_end = datetime.combine(date_obj.date(), max_time).replace(tzinfo=user_tz)
        else:
            # Parse start and end times
            start_time_obj = datetime.strptime(data["start_time"], "%H:%M").time()
            end_time_obj = datetime.strptime(data["end_time"], "%H:%M").time()

            # Combine date and times
            local_datetime_start = datetime.combine(date_obj.date(), start_time_obj).replace(tzinfo=user_tz)
            local_datetime_end = datetime.combine(date_obj.date(), end_time_obj).replace(tzinfo=user_tz)

            # If end time is before start time, assume it's the next day
            if local_datetime_end <= local_datetime_start:
                local_datetime_end += timedelta(days=1)

        # Convert to UTC
        utc_datetime_start = local_datetime_start.astimezone(UTC)
        utc_datetime_end = local_datetime_end.astimezone(UTC)

        # Generate UID
        event_uid = str(uuid.uuid4())

        # Create event
        event_schema = EventCreateSchema(
            user_id=user_id,
            uid=event_uid,
            calendar_id=local_calendar.id,
            date_start=utc_datetime_start,
            date_end=utc_datetime_end,
            all_day=all_day,
            need_to_remind=True,
            rrule=None,
            rdate=None,
            exdate=None,
            title=data["title"],
            description=data.get("description"),
        )

        await store.EventService.create(event_schema)

        await query.answer(t("create_event.confirmed", lang=settings.lang))
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            t("create_event.success", lang=settings.lang),
            back_button("menu_events", lang=settings.lang),
            parse_mode="HTML",
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error creating event for user {user_id}: {e}", exc_info=e)
        await query.answer(t("create_event.error", lang=settings.lang), show_alert=True)
        await edit_message(
            bot=query.bot,
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            state=state,
            text=(
                t("create_event.preview.title", lang=settings.lang)
                + "\n\n"
                + t("create_event.error", lang=settings.lang)
            ),
            reply_markup=event_confirmation_inline(lang=settings.lang),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "reject_event", StateFilter(CreateEventStates.waiting_for_confirmation))
async def reject_event(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Reject event creation and return to events menu."""
    await state.clear()
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        t("create_event.cancelled", lang=settings.lang),
        back_button("menu_events", lang=settings.lang),
        parse_mode="HTML",
    )
