"""Handlers for editing events through dialog."""

from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import back_button, skip_inline, start_time_inline
from logger.logger import logger
from middlewares.settings_middleware import SettingsData
from repositories.schemas import EventUpdateSchema
from states.states import EditEventStates
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


def format_datetime_for_display(dt: datetime | None, user_tz, lang: str) -> str:
    """Format datetime for display in user's timezone.

    Args:
        dt: Datetime to format (UTC).
        user_tz: User's timezone.
        lang: Language code.

    Returns:
        Formatted datetime string.
    """
    if dt is None:
        return t("events.view.event.date.none", lang=lang)
    local_dt = dt.astimezone(user_tz)
    return local_dt.strftime("%d.%m.%Y %H:%M")


@router.callback_query(F.data == "edit_event_cancel", StateFilter(EditEventStates))
async def cancel_event_edit(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Cancel event editing."""
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


@router.callback_query(F.data == "edit_event_skip_title", StateFilter(EditEventStates.waiting_for_new_title))
async def skip_edit_title(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Skip editing title."""
    await state.update_data(new_title=None)
    await state.set_state(EditEventStates.waiting_for_new_description)

    text = (
        f"{t('events.edit.enter_description', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        skip_inline("edit_event_skip_description", "edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(EditEventStates.waiting_for_new_title))
async def process_edit_title(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process edited event title."""
    title = message.text
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if title is None or len(title) == 0:
        text = (
            f"{t('events.edit.enter_title', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.title_empty', lang=settings.lang)}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            skip_inline("edit_event_skip_title", "edit_event_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    if len(title) > 100:
        text = (
            f"{t('events.edit.enter_title', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.title_too_long', lang=settings.lang)}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            skip_inline("edit_event_skip_title", "edit_event_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(new_title=title)
    await state.set_state(EditEventStates.waiting_for_new_description)

    text = (
        f"{t('events.edit.enter_description', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        skip_inline("edit_event_skip_description", "edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(
    F.data == "edit_event_skip_description", StateFilter(EditEventStates.waiting_for_new_description)
)
async def skip_edit_description(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Skip editing description."""
    await state.update_data(new_description=None)
    await state.set_state(EditEventStates.waiting_for_new_start_date)

    text = (
        f"{t('events.edit.enter_start_date', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        skip_inline("edit_event_skip_start_date", "edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(EditEventStates.waiting_for_new_description))
async def process_edit_description(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process edited event description."""
    description = message.text
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    await state.update_data(new_description=description)
    await state.set_state(EditEventStates.waiting_for_new_start_date)

    text = (
        f"{t('events.edit.enter_start_date', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        skip_inline("edit_event_skip_start_date", "edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "edit_event_skip_start_date", StateFilter(EditEventStates.waiting_for_new_start_date))
async def skip_edit_start_date(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Skip editing start date."""
    await state.update_data(new_start_date=None)
    await state.set_state(EditEventStates.waiting_for_new_start_time)

    text = (
        f"{t('events.edit.enter_start_time', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        start_time_inline("edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(EditEventStates.waiting_for_new_start_date))
async def process_edit_start_date(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process edited event start date."""
    date_str = message.text
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if date_str is None or not is_valid_date(date_str.strip()):
        text = (
            f"{t('events.edit.enter_start_date', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.date_format_error', lang=settings.lang, user_input=date_str or '')}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            skip_inline("edit_event_skip_start_date", "edit_event_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(new_start_date=date_str.strip())
    await state.set_state(EditEventStates.waiting_for_new_start_time)

    text = (
        f"{t('events.edit.enter_start_time', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        start_time_inline("edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "event_all_day", StateFilter(EditEventStates.waiting_for_new_start_time))
async def process_edit_all_day(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process all day event selection during edit."""
    await state.update_data(new_all_day=True, new_start_time=None, new_end_time=None)
    await state.set_state(EditEventStates.waiting_for_edit_confirmation)
    await show_edit_preview(query, state, store, settings)


@router.callback_query(F.data == "edit_event_skip_start_time", StateFilter(EditEventStates.waiting_for_new_start_time))
async def skip_edit_start_time(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Skip editing start time."""
    await state.update_data(new_start_time=None)
    await state.set_state(EditEventStates.waiting_for_new_end_date)

    text = (
        f"{t('events.edit.enter_end_date', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        skip_inline("edit_event_skip_end_date", "edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(EditEventStates.waiting_for_new_start_time))
async def process_edit_start_time(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process edited event start time."""
    time_str = message.text
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if time_str is None or not is_valid_time_hhmm(time_str.strip()):
        text = (
            f"{t('events.edit.enter_start_time', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.time_format_error', lang=settings.lang, user_input=time_str or '')}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            start_time_inline("edit_event_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    await state.update_data(new_start_time=time_str.strip(), new_all_day=False)
    await state.set_state(EditEventStates.waiting_for_new_end_date)

    text = (
        f"{t('events.edit.enter_end_date', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        skip_inline("edit_event_skip_end_date", "edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "edit_event_skip_end_date", StateFilter(EditEventStates.waiting_for_new_end_date))
async def skip_edit_end_date(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Skip editing end date."""
    await state.update_data(new_end_date=None)
    await state.set_state(EditEventStates.waiting_for_new_end_time)

    text = (
        f"{t('events.edit.enter_end_time', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text,
        skip_inline("edit_event_skip_end_time", "edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.message(StateFilter(EditEventStates.waiting_for_new_end_date))
async def process_edit_end_date(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process edited event end date."""
    date_str = message.text
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if date_str is None or not is_valid_date(date_str.strip()):
        text = (
            f"{t('events.edit.enter_end_date', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.date_format_error', lang=settings.lang, user_input=date_str or '')}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            skip_inline("edit_event_skip_end_date", "edit_event_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    # Validate that end date is not before start date
    data = await state.get_data()
    new_start_date_str = data.get("new_start_date")
    original_start_date_str = data.get("original_start_date")
    start_date_str = new_start_date_str or original_start_date_str

    if start_date_str:
        try:
            # Parse original start date from ISO format
            if isinstance(start_date_str, str) and "T" in start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00")).date()
            else:
                start_date = datetime.strptime(start_date_str, "%d.%m.%Y").date()
            end_date = datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
            if end_date < start_date:
                text = (
                    f"{t('events.edit.enter_end_date', lang=settings.lang)}\n\n"
                    f"<i>{t('create_event.end_date_before_start', lang=settings.lang)}</i>"
                )
                await edit_message(
                    message.bot,
                    message.chat.id,
                    last_message,
                    state,
                    text,
                    skip_inline("edit_event_skip_end_date", "edit_event_cancel", lang=settings.lang),
                    parse_mode="HTML",
                )
                return
        except (ValueError, AttributeError):
            pass

    await state.update_data(new_end_date=date_str.strip())
    await state.set_state(EditEventStates.waiting_for_new_end_time)

    text = (
        f"{t('events.edit.enter_end_time', lang=settings.lang)}\n\n"
        f"<i>{t('events.edit.skip_hint', lang=settings.lang)}</i>"
    )
    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        text,
        skip_inline("edit_event_skip_end_time", "edit_event_cancel", lang=settings.lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "edit_event_skip_end_time", StateFilter(EditEventStates.waiting_for_new_end_time))
async def skip_edit_end_time(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Skip editing end time."""
    await state.update_data(new_end_time=None)
    await state.set_state(EditEventStates.waiting_for_edit_confirmation)
    await show_edit_preview(query, state, store, settings)


@router.message(StateFilter(EditEventStates.waiting_for_new_end_time))
async def process_edit_end_time(message: Message, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Process edited event end time."""
    time_str = message.text
    await message.delete()
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    if time_str is None or not is_valid_time_hhmm(time_str.strip()):
        text = (
            f"{t('events.edit.enter_end_time', lang=settings.lang)}\n\n"
            f"<i>{t('create_event.time_format_error', lang=settings.lang, user_input=time_str or '')}</i>"
        )
        await edit_message(
            message.bot,
            message.chat.id,
            last_message,
            state,
            text,
            skip_inline("edit_event_skip_end_time", "edit_event_cancel", lang=settings.lang),
            parse_mode="HTML",
        )
        return

    # Validate that end datetime is not before start datetime
    data = await state.get_data()
    user_tz = parse_user_timezone(settings.timezone)
    new_start_date_str = data.get("new_start_date")
    new_start_time_str = data.get("new_start_time")
    original_start_date_str = data.get("original_start_date")
    original_start_time_str = data.get("original_start_time")

    start_date_str = new_start_date_str or original_start_date_str
    start_time_str = new_start_time_str or original_start_time_str
    end_date_str = data.get("new_end_date") or data.get("original_end_date")

    if start_date_str and start_time_str and end_date_str:
        try:
            # Parse start date
            if isinstance(start_date_str, str) and "T" in start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00")).date()
            else:
                start_date = datetime.strptime(start_date_str, "%d.%m.%Y").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            start_datetime = datetime.combine(start_date, start_time).replace(tzinfo=user_tz)

            # Parse end date
            if isinstance(end_date_str, str) and "T" in end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00")).date()
            else:
                end_date = datetime.strptime(end_date_str, "%d.%m.%Y").date()
            end_time = datetime.strptime(time_str.strip(), "%H:%M").time()
            end_datetime = datetime.combine(end_date, end_time).replace(tzinfo=user_tz)

            if end_datetime <= start_datetime:
                text = (
                    f"{t('events.edit.enter_end_time', lang=settings.lang)}\n\n"
                    f"<i>{t('create_event.end_datetime_before_start', lang=settings.lang)}</i>"
                )
                await edit_message(
                    message.bot,
                    message.chat.id,
                    last_message,
                    state,
                    text,
                    skip_inline("edit_event_skip_end_time", "edit_event_cancel", lang=settings.lang),
                    parse_mode="HTML",
                )
                return
        except (ValueError, AttributeError):
            pass

    await state.update_data(new_end_time=time_str.strip())
    await state.set_state(EditEventStates.waiting_for_edit_confirmation)

    # Show preview
    last_message = await get_last_message_id(state)
    if last_message is None:
        logger.error("Last message is not found", extra={"state": await state.get_data()})
        return

    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        logger.error("Event id is not found", extra={"state": data})
        return

    # Get original event
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        return

    user_tz = parse_user_timezone(settings.timezone)
    preview_text = build_preview_text(data, event, user_tz, settings.lang)

    await state.set_state(EditEventStates.waiting_for_edit_confirmation)
    from keyboards.inline import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = [
        [
            InlineKeyboardButton(text=t("btn.accept", lang=settings.lang), callback_data="edit_event_confirm"),
            InlineKeyboardButton(text=t("btn.reject", lang=settings.lang), callback_data="edit_event_cancel"),
        ]
    ]
    confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await edit_message(
        message.bot,
        message.chat.id,
        last_message,
        state,
        preview_text,
        confirmation_keyboard,
        parse_mode="HTML",
    )


async def show_edit_preview(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Show preview of event changes from callback query."""
    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        logger.error("Event id is not found", extra={"state": data})
        return

    # Get original event
    event = await store.EventService.get_by_id(event_id)
    if event is None:
        logger.error("Event is not found", extra={"event_id": event_id})
        return

    user_tz = parse_user_timezone(settings.timezone)
    preview_text = build_preview_text(data, event, user_tz, settings.lang)

    await state.set_state(EditEventStates.waiting_for_edit_confirmation)
    from keyboards.inline import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = [
        [
            InlineKeyboardButton(text=t("btn.accept", lang=settings.lang), callback_data="edit_event_confirm"),
            InlineKeyboardButton(text=t("btn.reject", lang=settings.lang), callback_data="edit_event_cancel"),
        ]
    ]
    confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        preview_text,
        confirmation_keyboard,
        parse_mode="HTML",
    )


def build_preview_text(data: dict, event, user_tz, lang: str) -> str:
    """Build preview text showing old and new values.

    Args:
        data: State data with original and new values.
        event: Original event object.
        user_tz: User's timezone.
        lang: Language code.

    Returns:
        Preview text string.
    """
    preview_lines = [t("events.edit.preview.title", lang=lang), ""]

    # Title
    original_title = data.get("original_title") or t("events.view.event.title.none", lang=lang)
    new_title = data.get("new_title")
    if new_title is not None:
        preview_lines.append(
            f"<b>Title:</b>\n"
            f"{t('events.edit.preview.old_new', lang=lang, old_value=original_title, new_value=new_title)}"
        )
    else:
        preview_lines.append(f"<b>Title:</b>\n{t('events.edit.preview.unchanged', lang=lang, value=original_title)}")

    # Description
    original_description = data.get("original_description") or t("create_event.preview.description_none", lang=lang)
    new_description = data.get("new_description")
    if new_description is not None:
        preview_lines.append(
            f"<b>Description:</b>\n"
            f"{t('events.edit.preview.old_new', lang=lang, old_value=original_description, new_value=new_description)}"
        )
    else:
        preview_lines.append(
            f"<b>Description:</b>\n{t('events.edit.preview.unchanged', lang=lang, value=original_description)}"
        )

    # Start date/time
    original_start = event.date_start
    original_start_str = format_datetime_for_display(original_start, user_tz, lang)
    new_start_date_str = data.get("new_start_date")
    new_start_time_str = data.get("new_start_time")
    if new_start_date_str or new_start_time_str:
        # Build new start datetime
        if new_start_date_str:
            start_date_obj = datetime.strptime(new_start_date_str, "%d.%m.%Y")
            if new_start_time_str:
                start_time_obj = datetime.strptime(new_start_time_str, "%H:%M").time()
                new_start = datetime.combine(start_date_obj.date(), start_time_obj).replace(tzinfo=user_tz)
            else:
                new_start = datetime.combine(start_date_obj.date(), datetime.min.time()).replace(tzinfo=user_tz)
            new_start_str = new_start.strftime("%d.%m.%Y %H:%M")
        else:
            new_start_str = original_start_str
        preview_lines.append(
            f"<b>Start:</b>\n"
            f"{t('events.edit.preview.old_new', lang=lang, old_value=original_start_str, new_value=new_start_str)}"
        )
    else:
        preview_lines.append(
            f"<b>Start:</b>\n{t('events.edit.preview.unchanged', lang=lang, value=original_start_str)}"
        )

    # End date/time
    original_end = event.date_end
    original_end_str = format_datetime_for_display(original_end, user_tz, lang)
    new_end_date_str = data.get("new_end_date")
    new_end_time_str = data.get("new_end_time")
    if new_end_date_str or new_end_time_str:
        # Build new end datetime
        if new_end_date_str:
            end_date_obj = datetime.strptime(new_end_date_str, "%d.%m.%Y")
            if new_end_time_str:
                end_time_obj = datetime.strptime(new_end_time_str, "%H:%M").time()
                new_end = datetime.combine(end_date_obj.date(), end_time_obj).replace(tzinfo=user_tz)
            else:
                new_end = datetime.combine(end_date_obj.date(), datetime.max.time()).replace(tzinfo=user_tz)
            new_end_str = new_end.strftime("%d.%m.%Y %H:%M")
        else:
            new_end_str = original_end_str
        preview_lines.append(
            f"<b>End:</b>\n"
            f"{t('events.edit.preview.old_new', lang=lang, old_value=original_end_str, new_value=new_end_str)}"
        )
    else:
        preview_lines.append(f"<b>End:</b>\n{t('events.edit.preview.unchanged', lang=lang, value=original_end_str)}")

    # All day
    original_all_day = data.get("original_all_day", False)
    new_all_day = data.get("new_all_day")
    if new_all_day is not None:
        old_all_day_str = "Yes" if original_all_day else "No"
        new_all_day_str = "Yes" if new_all_day else "No"
        preview_lines.append(
            f"<b>All Day:</b>\n"
            f"{t('events.edit.preview.old_new', lang=lang, old_value=old_all_day_str, new_value=new_all_day_str)}"
        )
    else:
        all_day_str = "Yes" if original_all_day else "No"
        preview_lines.append(
            f"<b>All Day:</b>\n"
            f"{t('events.edit.preview.unchanged', lang=lang, value=all_day_str)}"
        )

    preview_text = "\n".join(preview_lines)
    preview_text += f"\n\n<i>{t('create_event.preview.confirm', lang=lang)}</i>"
    return preview_text


@router.callback_query(F.data == "edit_event_confirm", StateFilter(EditEventStates.waiting_for_edit_confirmation))
async def confirm_event_edit(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Confirm and save event changes."""
    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        logger.error("Event id is not found", extra={"state": data})
        await query.answer(t("events.edit.error.not_found", lang=settings.lang), show_alert=True)
        return

    # Build update schema
    update_data = {}
    if "new_title" in data and data["new_title"] is not None:
        update_data["title"] = data["new_title"]
    if "new_description" in data and data["new_description"] is not None:
        update_data["description"] = data["new_description"]

    user_tz = parse_user_timezone(settings.timezone)

    if "new_start_date" in data and data["new_start_date"] is not None:
        start_date_obj = datetime.strptime(data["new_start_date"], "%d.%m.%Y")
        if "new_start_time" in data and data["new_start_time"] is not None:
            start_time_obj = datetime.strptime(data["new_start_time"], "%H:%M").time()
            local_datetime_start = datetime.combine(start_date_obj.date(), start_time_obj).replace(tzinfo=user_tz)
        else:
            local_datetime_start = datetime.combine(start_date_obj.date(), datetime.min.time()).replace(tzinfo=user_tz)
        update_data["date_start"] = local_datetime_start.astimezone(UTC)
    elif "new_start_time" in data and data["new_start_time"] is not None:
        # Only time changed, need to get original date
        original_start = data.get("original_date_start")
        if original_start:
            if isinstance(original_start, str) and "T" in original_start:
                original_start_dt = datetime.fromisoformat(original_start.replace("Z", "+00:00"))
            else:
                original_start_dt = datetime.fromisoformat(original_start)
            original_start_local = original_start_dt.astimezone(user_tz)
            start_time_obj = datetime.strptime(data["new_start_time"], "%H:%M").time()
            local_datetime_start = datetime.combine(original_start_local.date(), start_time_obj).replace(tzinfo=user_tz)
            update_data["date_start"] = local_datetime_start.astimezone(UTC)

    if "new_end_date" in data and data["new_end_date"] is not None:
        end_date_obj = datetime.strptime(data["new_end_date"], "%d.%m.%Y")
        if "new_end_time" in data and data["new_end_time"] is not None:
            end_time_obj = datetime.strptime(data["new_end_time"], "%H:%M").time()
            local_datetime_end = datetime.combine(end_date_obj.date(), end_time_obj).replace(tzinfo=user_tz)
        else:
            local_datetime_end = datetime.combine(end_date_obj.date(), datetime.max.time()).replace(tzinfo=user_tz)
        update_data["date_end"] = local_datetime_end.astimezone(UTC)
    elif "new_end_time" in data and data["new_end_time"] is not None:
        # Only time changed, need to get original date
        original_end = data.get("original_date_end")
        if original_end:
            if isinstance(original_end, str) and "T" in original_end:
                original_end_dt = datetime.fromisoformat(original_end.replace("Z", "+00:00"))
            else:
                original_end_dt = datetime.fromisoformat(original_end)
            original_end_local = original_end_dt.astimezone(user_tz)
            end_time_obj = datetime.strptime(data["new_end_time"], "%H:%M").time()
            local_datetime_end = datetime.combine(original_end_local.date(), end_time_obj).replace(tzinfo=user_tz)
            update_data["date_end"] = local_datetime_end.astimezone(UTC)

    if "new_all_day" in data:
        update_data["all_day"] = data["new_all_day"]

    if not update_data:
        await query.answer(t("events.edit.no_changes", lang=settings.lang), show_alert=True)
        return

    try:
        update_schema = EventUpdateSchema(**update_data)
        await store.EventService.update_by_id(event_id, update_schema)
        await query.answer(t("events.edit.success", lang=settings.lang), show_alert=False)
        await state.clear()
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            t("events.edit.success", lang=settings.lang),
            back_button("menu_events", lang=settings.lang),
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Error updating event: {e}", exc_info=e)
        await query.answer(t("events.edit.error.failed", lang=settings.lang), show_alert=True)
