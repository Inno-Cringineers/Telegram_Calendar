from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from i18n.strings import t
from keyboards.inline import get_back_button, get_calendar_menu_inline
from logger.logger import logger
from states.states import CalendarLinkingStates

router = Router()


@router.callback_query(F.data == "menu_link_calendar")
async def open_calendar_menu(query: CallbackQuery, state: FSMContext) -> None:
    """Open calendar linking menu."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} opened calendar menu")

    # TODO: Get user language from settings when session is available
    lang = "ru"

    await state.set_state(CalendarLinkingStates.in_calendar_menu)

    if query.message and hasattr(query.message, "edit_text"):
        await query.message.edit_text(
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
    lang = "ru"

    await state.set_state(CalendarLinkingStates.in_calendar_list)
    await query.answer(t("calendar.list.answer", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
        text = (
            f"{t('calendar.list.title', lang=lang)}\n\n"
            f"{t('calendar.list.linked', lang=lang)}\n"
            "1. 📅 Personal (Google Calendar)\n"
            "2. 💼 Work (Outlook Calendar)\n"
            "3. 🎯 Projects (Yandex Calendar)\n\n"
            f"<i>{t('calendar.list.feature_dev', lang=lang)}</i>"
        )
        await query.message.edit_text(
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
    lang = "ru"

    await state.set_state(CalendarLinkingStates.waiting_for_calendar_link)
    await query.answer(t("calendar.new.answer", lang=lang))

    if query.message and hasattr(query.message, "edit_text"):
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
