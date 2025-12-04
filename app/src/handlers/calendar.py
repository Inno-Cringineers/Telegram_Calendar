from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import back_button, calendar_inline, calendar_menu_inline
from logger.logger import logger
from repositories.schemas import CalendarFilter
from states.states import CalendarLinkingStates
from store.store import Store
from utils.handlers import edit_message, log_action, send_clean_message

router = Router()


@router.callback_query(F.data == "menu_link_calendar")
@log_action("User opened calendar linking menu")
async def open_calendar_menu(query: CallbackQuery, state: FSMContext, lang: str, **kwargs) -> None:
    """Open calendar linking menu."""
    await state.set_state(CalendarLinkingStates.in_calendar_menu)

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    await edit_message(
        query.message,
        state,
        f"{t('calendar_link_title', lang=lang)}\n\n{t('calendar_link_description', lang=lang)}",
        calendar_menu_inline(lang=lang),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "calendar_list", CalendarLinkingStates.in_calendar_menu)
async def calendar_list(query: CallbackQuery, state: FSMContext, store: Store, lang: str, **kwargs) -> None:
    """Show list of linked calendars."""
    calendars = await store.CalendarRepository.find(CalendarFilter(user_id=query.from_user.id))  # type: ignore[call-arg]

    # remove local calendars from list
    calendars = [calendar for calendar in calendars if calendar.url is not None]

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    if len(calendars) == 0:
        await edit_message(
            query.message,
            state,
            text=f"{t('calendar_list_title', lang=lang)}\n\n{t('calendar_list_no_calendars', lang=lang)}",
            parse_mode="HTML",
            reply_markup=back_button("menu_link_calendar", lang=lang),
        )
        return

    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return

    await edit_message(
        query.message,
        state,
        text=t("calendar_list_title", lang=lang),
        parse_mode="HTML",
        reply_markup=None,
    )

    for calendar in calendars:
        sync = "✅" if calendar.sync_enabled else "❌"
        await send_clean_message(
            query.message,
            state,
            t(
                "calendar.message",
                lang=lang,
                calendar_name=calendar.name,
                link=calendar.url,  # type: ignore[arg-type]
                enabled=sync,
            ),
            parse_mode="HTML",
            reply_markup=calendar_inline(linked=calendar.sync_enabled, calendar_id=calendar.id, lang=lang),  # type: ignore[arg-type]
        )


# Каждое сообщение сохранять в state
# Для каждого сообщения устанавливать флаг "delete keyboard", "delete message"
# Затем когда нужно, пробегаться по сообщениям и удалять те, что помечены delete_message, удалять клавиатуры для тех, кто "delete_keyboard"
#
@router.callback_query(F.data == "calendar_new", CalendarLinkingStates.in_calendar_menu)
async def calendar_new(query: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Link a new calendar."""
    user_id = query.from_user.id
    logger.info(f"User {user_id} initiated linking new calendar")

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
            reply_markup=back_button(lang=lang),
        )


@router.message(CalendarLinkingStates.waiting_for_calendar_link)
async def process_calendar_link(message: Message, state: FSMContext, lang: str) -> None:
    """Process calendar link."""

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
        reply_markup=back_button(lang=lang),
    )


@router.message(CalendarLinkingStates.waiting_for_calendar_name)
async def process_calendar_name(message: Message, state: FSMContext, lang: str) -> None:
    """Process calendar name."""
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
        reply_markup=back_button("calendar_confirm", lang=lang),
    )


@router.callback_query(F.data == "calendar_confirm", CalendarLinkingStates.waiting_for_calendar_confirmation)
async def calendar_confirm(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Confirm calendar linking."""

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
            reply_markup=calendar_menu_inline(lang=lang),
        )
    else:
        await query.answer(t("calendar.link.success", lang=lang))
