from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import (
    get_back_button,
    get_cancel_keyboard,
    get_event_confirmation_inline,
    get_skip_keyboard,
)
from logger.logger import logger
from states.states import CreateEventStates, EventsMenuStates

router = Router()


def is_valid_date(date_str: str) -> bool:
    """Validate date format DD.MM.YYYY."""
    try:
        event_date = datetime.strptime(date_str, "%d.%m.%Y")
        # Check if date is not in the past
        if event_date.date() < datetime.now().date():
            return False
        return True
    except ValueError:
        return False


def is_valid_time(time_str: str) -> bool:
    """Validate time format HH:MM."""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


@router.callback_query(F.data == "create_new_event", EventsMenuStates.in_events_create)
async def process_create_new_event_callback(query: CallbackQuery, state: FSMContext) -> None:
    """Transition beetween states."""
    user_name = query.from_user.first_name
    user_id = query.from_user.id
    logger.info(f"User {user_name} (ID: {user_id}) creating event")

    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.set_state(CreateEventStates.waiting_for_title)

    if isinstance(query.message, Message):
        await query.message.edit_text(
            t("create_event.enter_title", lang=lang),
            reply_markup=get_cancel_keyboard("events_cancel", lang=lang),
        )


@router.callback_query(F.data == "events_cancel", StateFilter(CreateEventStates))
async def cancel_event_creation(query: CallbackQuery, state: FSMContext) -> None:
    """Cancel event creation."""
    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.clear()
    if isinstance(query.message, Message):
        await query.message.edit_text(
            t("create_event.cancelled", lang=lang),
            reply_markup=get_back_button("menu_events", lang=lang),
        )


@router.message(CreateEventStates.waiting_for_title)
async def process_event_title(message: Message, state: FSMContext) -> None:
    """Process event title."""
    # TODO: Get user language from settings when session is available
    lang = "ru"

    title = message.text
    if title is None or len(title) == 0:
        await message.answer(t("create_event.title_empty", lang=lang))
        return

    if len(title) > 100:
        await message.answer(t("create_event.title_too_long", lang=lang))
        return

    await state.update_data(title=title)
    await state.set_state(CreateEventStates.waiting_for_description)

    await message.answer(
        t("create_event.enter_description", lang=lang),
        reply_markup=get_skip_keyboard(skip_callback="skip_description", cancel_callback="events_cancel", lang=lang),
    )


@router.message(CreateEventStates.waiting_for_description)
async def process_event_description(message: Message, state: FSMContext) -> None:
    """Process event description."""
    # TODO: Get user language from settings when session is available
    lang = "ru"

    description = message.text

    await state.update_data(description=description)

    await state.set_state(CreateEventStates.waiting_for_start_date)
    await message.answer(
        t("create_event.enter_date", lang=lang),
        reply_markup=get_cancel_keyboard("events_cancel", lang=lang),
    )


@router.callback_query(F.data == "skip_description", CreateEventStates.waiting_for_description)
async def skip_event_description(query: CallbackQuery, state: FSMContext) -> None:
    """Skip event description step."""
    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.update_data(description=None)
    await state.set_state(CreateEventStates.waiting_for_start_date)

    if isinstance(query.message, Message):
        await query.message.edit_text(
            t("create_event.enter_date", lang=lang),
            reply_markup=get_cancel_keyboard("events_cancel", lang=lang),
        )


@router.message(CreateEventStates.waiting_for_start_date)
async def process_event_date(message: Message, state: FSMContext) -> None:
    """Process event date with validation."""
    # TODO: Get user language from settings when session is available
    lang = "ru"

    if message.text is None:
        await message.answer(
            t("create_event.date_format_error", lang=lang),
            reply_markup=get_cancel_keyboard("events_cancel", lang=lang),
        )
        return

    date_str = message.text.strip()

    if not is_valid_date(date_str):
        await message.answer(
            t("create_event.date_format_error", lang=lang),
            reply_markup=get_cancel_keyboard("events_cancel", lang=lang),
        )
        return

    await state.update_data(start_date=date_str)
    await state.set_state(CreateEventStates.waiting_for_start_time)
    await message.answer(
        t("create_event.enter_time", lang=lang),
        reply_markup=get_cancel_keyboard("events_cancel", lang=lang),
    )


@router.message(CreateEventStates.waiting_for_start_time)
async def process_event_time(message: Message, state: FSMContext) -> None:
    """Process event time with validation."""
    # TODO: Get user language from settings when session is available
    lang = "ru"

    if message.text is None:
        await message.answer(t("create_event.time_format_error", lang=lang))
        return

    time_str = message.text.strip()

    if not is_valid_time(time_str):
        await message.answer(t("create_event.time_format_error", lang=lang))
        return

    data = await state.get_data()
    await state.update_data(start_time=time_str)

    # Show preview of the event
    description_text = (
        data["description"] if data["description"] else t("create_event.preview.description_none", lang=lang)
    )
    preview_text = (
        f"{t('create_event.preview.title', lang=lang)}\n\n"
        f"{t('create_event.preview.title_label', lang=lang, title=data['title'])}\n"
        f"{t('create_event.preview.description_label', lang=lang, description=description_text)}\n"
        f"{t('create_event.preview.date_label', lang=lang, date=data['start_date'])}\n"
        f"{t('create_event.preview.time_label', lang=lang, time=time_str)}\n\n"
        f"{t('create_event.preview.confirm', lang=lang)}"
    )

    await state.set_state(CreateEventStates.waiting_for_confirmation)
    await message.answer(
        preview_text,
        parse_mode="HTML",
        reply_markup=get_event_confirmation_inline(lang=lang),
    )


@router.callback_query(F.data == "confirm_event", CreateEventStates.waiting_for_confirmation)
async def confirm_event(query: CallbackQuery, state: FSMContext) -> None:
    """Confirm and save event."""
    # TODO: Get user language from settings when session is available
    lang = "ru"

    data = await state.get_data()
    user_id = query.from_user.id

    logger.info(
        f"User {user_id} confirmed event creation: "
        f"title={data['title']}, date={data['start_date']}, "
        f"time={data['start_time']}"
    )

    # TODO: Save event to database
    # await save_event(user_id, data)

    await query.answer(t("create_event.confirmed", lang=lang))
    if isinstance(query.message, Message):
        await query.message.edit_text(
            t("create_event.success", lang=lang),
            parse_mode="HTML",
            reply_markup=get_back_button("menu_events", lang=lang),
        )
    await state.clear()
