from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import get_back_button, get_calendar_menu_inline
from logger.logger import logger
from states.states import CalendarLinkingStates
from store.store import Store

router = Router()


@router.callback_query(F.data == "menu_link_calendar")
async def open_calendar_menu(query: CallbackQuery, state: FSMContext) -> None:
    """Open calendar linking menu."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} opened calendar menu")

    # TODO: Get user language from settings when session is available
    lang = "en"

    await state.set_state(CalendarLinkingStates.in_calendar_menu)

    message = query.message
    if message and isinstance(message, Message):
        await message.edit_text(
            t("calendar.link.title", lang=lang),
            parse_mode="HTML",
            reply_markup=get_calendar_menu_inline(lang=lang),
        )


@router.callback_query(F.data == "calendar_list", CalendarLinkingStates.in_calendar_menu)
async def calendar_list(query: CallbackQuery, state: FSMContext) -> None:
    """Show list of linked calendars."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} viewing calendar list")

    # TODO: Get user language from settings when session is available
    lang = "en"

    await state.set_state(CalendarLinkingStates.in_calendar_list)
    await query.answer(t("calendar.list.answer", lang=lang))

    message = query.message
    if message and isinstance(message, Message):
        text = (
            f"{t('calendar.list.title', lang=lang)}\n\n"
            f"{t('calendar.list.linked', lang=lang)}\n"
            "1. 📅 Personal (Google Calendar)\n"
            "2. 💼 Work (Outlook Calendar)\n"
            "3. 🎯 Projects (Yandex Calendar)\n\n"
            f"<i>{t('calendar.list.feature_dev', lang=lang)}</i>"
        )
        await message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button(lang=lang),
        )


@router.callback_query(F.data == "calendar_new", CalendarLinkingStates.in_calendar_menu)
async def calendar_new(query: CallbackQuery, state: FSMContext) -> None:
    """Link a new calendar."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} initiated linking new calendar")

    # TODO: Get user language from settings when session is available
    lang = "en"

    await state.set_state(CalendarLinkingStates.waiting_for_calendar_link)
    await query.answer(t("calendar.new.answer", lang=lang))

    if query.message and isinstance(query.message, Message):
        text = (
            f"{t('calendar.new.title', lang=lang)}\n\n"
            f"{t('calendar.new.enter_link', lang=lang)}\n\n"
            f"<i>{t('events.feature_dev', lang=lang)}</i>"
        )
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_back_button(lang=lang),
        )


@router.message(CalendarLinkingStates.waiting_for_calendar_link)
async def process_calendar_link(message: Message, state: FSMContext) -> None:
    """Process calendar link."""
    # TODO: Get user language from settings when session is available
    lang = "en"

    url = message.text
    if url is None or len(url) == 0:
        await message.answer(t("calendar.link.url_empty", lang=lang))
        return

    if len(url) > 255:
        await message.answer(t("calendar.link.url_too_long", lang=lang))
        return

    await state.update_data(url=url)
    await state.set_state(CalendarLinkingStates.waiting_for_calendar_name)
    await message.answer(t("calendar.link.enter_name", lang=lang))
    await message.answer(
        t("calendar.link.enter_name", lang=lang),
        reply_markup=get_back_button(lang=lang),
    )


@router.message(CalendarLinkingStates.waiting_for_calendar_name)
async def process_calendar_name(message: Message, state: FSMContext) -> None:
    """Process calendar name."""
    # TODO: Get user language from settings when session is available
    lang = "en"
    name = message.text
    if name is None or len(name) == 0:
        await message.answer(t("calendar.link.name_empty", lang=lang))
        return

    if len(name) > 255:
        await message.answer(t("calendar.link.name_too_long", lang=lang))
        return

    await state.update_data(name=name)
    await state.set_state(CalendarLinkingStates.waiting_for_calendar_confirmation)
    await message.answer(t("calendar.link.confirm_link", lang=lang))
    await message.answer(
        t("calendar.link.confirm_link", lang=lang),
        reply_markup=get_back_button("calendar_confirm", lang=lang),
    )


@router.callback_query(F.data == "calendar_confirm", CalendarLinkingStates.waiting_for_calendar_confirmation)
async def calendar_confirm(query: CallbackQuery, state: FSMContext, store: Store) -> None:
    """Confirm calendar linking."""
    # TODO: Get user language from settings when session is available
    lang = "en"

    # Get data from state
    state_data = await state.get_data()
    url: str | None = state_data.get("url")
    name: str | None = state_data.get("name")

    # Get user_id
    user_id = query.from_user.id

    # Upload calendar if we have all required data
    if url and name:
        try:
            await store.UploadService.upload_ical_url(user_id, name, url)
            logger.info(f"User {user_id} successfully linked calendar: {name} ({url})")
        except Exception as e:
            logger.error(f"Error uploading calendar for user {user_id}: {e}", exc_info=e)
            await query.answer(t("calendar.link.error", lang=lang))
            return

    await state.set_state(CalendarLinkingStates.in_calendar_menu)
    await query.answer(t("calendar.link.confirmed", lang=lang))
    if query.message and isinstance(query.message, Message):
        await query.message.edit_text(
            t("calendar.link.success", lang=lang),
            parse_mode="HTML",
            reply_markup=get_calendar_menu_inline(lang=lang),
        )
    else:
        await query.answer(t("calendar.link.success", lang=lang))
