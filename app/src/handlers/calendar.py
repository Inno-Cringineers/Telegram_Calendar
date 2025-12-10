from datetime import UTC, datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from i18n.strings import t
from keyboards.inline import (
    back_button,
    calendar_inline,
    calendar_menu_inline,
    confirm_calendar_inline,
    confirm_calendar_rename_inline,
)
from logger.logger import logger
from middlewares.settings_middleware import SettingsData
from repositories.schemas import CalendarFilter, CalendarUpdateSchema
from states.states import CalendarLinkingStates
from store.store import Store
from utils.handlers import clean_messages, edit_message, get_last_message_id, get_messages, send_message

router = Router()


@router.callback_query(F.data == "menu_link_calendar")
async def open_calendar_menu(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Open calendar linking menu."""
    await state.set_state(CalendarLinkingStates.in_calendar_menu)
    await clean_messages(query.bot, query.message.chat.id, state)

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        f"{t('calendar_link_title', lang=settings.lang)}\n\n{t('calendar_link_description', lang=settings.lang)}",
        calendar_menu_inline(lang=settings.lang),
        parse_mode="HTML",
        delete_keyboard=True,
        delete_message=False,
    )


@router.callback_query(F.data == "calendar_list", StateFilter(CalendarLinkingStates.in_calendar_menu))
async def calendar_list(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Show list of linked calendars."""
    calendars = await store.CalendarService.get_external_calendars_by_user_id(query.from_user.id)

    if len(calendars) == 0:
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            text=f"{t('calendar_list_title', lang=settings.lang)}\n\n{t('calendar_list_no_calendars', lang=settings.lang)}",  # noqa: E501
            parse_mode="HTML",
            reply_markup=back_button("menu_link_calendar", lang=settings.lang),
        )
        return

    await query.message.delete()

    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        text=t("calendar_list_title", lang=settings.lang),
        parse_mode="HTML",
        reply_markup=None,
        delete_keyboard=False,
        delete_message=True,
    )

    for calendar in calendars:
        sync = "✅" if calendar.sync_enabled else "❌"
        await send_message(
            query.bot,
            query.message.chat.id,
            state,
            t(
                "calendar.message",
                lang=settings.lang,
                calendar_name=calendar.name,
                link=calendar.url,
                enabled=sync,
            ),
            parse_mode="HTML",
            reply_markup=calendar_inline(linked=calendar.sync_enabled, calendar_id=calendar.id, lang=settings.lang),
            delete_keyboard=False,
            delete_message=True,
            extra_data={"calendar_id": calendar.id},
        )

    await send_message(
        query.bot,
        query.message.chat.id,
        state,
        text=t("calendar_list_end", lang=settings.lang),
        parse_mode="HTML",
        reply_markup=back_button("menu_link_calendar", lang=settings.lang),
        delete_keyboard=True,
        delete_message=False,
    )


@router.callback_query(F.data.startswith("calendar_unlink:"), StateFilter(CalendarLinkingStates.in_calendar_menu))
async def calendar_unlink(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Unlink or link a calendar with immediate sync on enable."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    calendar_id = int(query.data.split(":")[1])

    calendar = await store.CalendarService.get_by_id(calendar_id)
    if calendar is None:
        logger.error("Calendar is not found", extra={"calendar_id": calendar_id})
        return

    # Check if we're enabling sync (was False, will be True)
    was_sync_enabled = calendar.sync_enabled
    will_enable_sync = not was_sync_enabled

    # If enabling sync, try to synchronize immediately (only for external calendars with URL)
    if will_enable_sync:
        if calendar.url is not None:
            try:
                # Try to synchronize the calendar
                await store.UploadService.upload_ical_url(calendar.user_id, calendar.name, calendar.url)
                # If successful, enable sync and update last_sync
                # Remove timezone info as database expects naive datetime
                now_utc = datetime.now(UTC).replace(tzinfo=None)
                calendar = await store.CalendarService.update(
                    calendar_id,
                    CalendarUpdateSchema(sync_enabled=True, last_sync=now_utc),
                )
                logger.info(f"Calendar {calendar_id} synchronized successfully and enabled")
            except Exception as e:
                logger.error(f"Error synchronizing calendar {calendar_id}: {e}", exc_info=e)
                # Show popup error message and keep sync_enabled=False
                await query.answer(t("calendar.sync.error", lang=settings.lang), show_alert=True)
                return
        else:
            # For local calendars (no URL), just enable sync without synchronization
            calendar = await store.CalendarService.update(
                calendar_id,
                CalendarUpdateSchema(sync_enabled=True),
            )
    else:
        # If disabling sync, just toggle it
        calendar = await store.CalendarService.unlink_calendar(calendar_id)
        if calendar is None:
            logger.error("Calendar is not found", extra={"calendar_id": calendar_id})
            return

    messages = await get_messages(state)

    message = None
    for msg in messages:
        if msg.get("extra_data", {}) is None:
            continue
        if msg.get("extra_data", {}).get("calendar_id") == calendar_id:
            message = msg
            break

    if message is None or message.get("message_id") is None:
        logger.error("Message is not found", extra={"calendar_id": calendar_id})
        return

    sync = "✅" if calendar.sync_enabled else "❌"
    await edit_message(
        query.bot,
        query.message.chat.id,
        message["message_id"],
        state,
        text=t(
            "calendar.message",
            lang=settings.lang,
            calendar_name=calendar.name,
            link=calendar.url,
            enabled=sync,
        ),
        parse_mode="HTML",
        reply_markup=calendar_inline(linked=calendar.sync_enabled, calendar_id=calendar_id, lang=settings.lang),
    )


@router.callback_query(F.data.startswith("calendar_delete:"), StateFilter(CalendarLinkingStates.in_calendar_menu))
async def calendar_delete(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Delete a calendar."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    calendar_id = int(query.data.split(":")[1])

    messages = await get_messages(state)

    message = None
    for msg in messages:
        if msg.get("extra_data", {}) is None:
            continue
        if msg.get("extra_data", {}).get("calendar_id") == calendar_id:
            message = msg
            break

    if message is None or message.get("message_id") is None:
        logger.error("Message is not found", extra={"calendar_id": calendar_id})
        return

    await store.CalendarService.delete(calendar_id)
    await query.bot.delete_message(chat_id=query.message.chat.id, message_id=message["message_id"])


@router.callback_query(F.data == "calendar_new", StateFilter(CalendarLinkingStates.in_calendar_menu))
async def calendar_new(query: CallbackQuery, state: FSMContext, settings: SettingsData) -> None:
    """Link a new calendar."""
    await state.set_state(CalendarLinkingStates.waiting_for_calendar_link)

    text = f"{t('calendar.new.title', lang=settings.lang)}\n\n{t('calendar.new.enter_link', lang=settings.lang)}\n\n"
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=text,
        parse_mode="HTML",
        reply_markup=back_button(lang=settings.lang),
    )


@router.message(StateFilter(CalendarLinkingStates.waiting_for_calendar_link))
async def process_calendar_link(message: Message, state: FSMContext, settings: SettingsData, store: Store) -> None:
    """Process calendar link."""

    last_message_id = await get_last_message_id(state)
    if last_message_id is None:
        logger.error("Last message id is not found", extra={"state": state})
        return

    url = message.text

    await message.delete()

    if url is None or len(url) == 0:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            text=(
                f"{t('calendar.new.title', lang=settings.lang)}\n\n"
                f"{t('calendar.link.url.empty', lang=settings.lang)}\n\n"
            ),
            parse_mode="HTML",
            reply_markup=back_button(lang=settings.lang),
        )
        return
    if len(url) > 255:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            text=(
                f"{t('calendar.new.title', lang=settings.lang)}\n\n"
                f"{t('calendar.link.url_too_long', lang=settings.lang)}\n\n"
            ),
            parse_mode="HTML",
            reply_markup=back_button(lang=settings.lang),
        )
        return

    if not url.startswith("http://") and not url.startswith("https://"):
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            text=(
                f"{t('calendar.new.title', lang=settings.lang)}\n\n"
                f"{t('calendar.link.url.invalid', lang=settings.lang)}\n\n"
            ),
            parse_mode="HTML",
            reply_markup=back_button(lang=settings.lang),
        )
        return

    # check if url is not exists in database for this user
    calendars = await store.CalendarService.find(CalendarFilter(url=url, user_id=message.from_user.id))
    if calendars != []:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            text=(
                f"{t('calendar.new.title', lang=settings.lang)}\n\n"
                f"{t('calendar.link.url.exists', lang=settings.lang)}\n\n"
            ),
            parse_mode="HTML",
            reply_markup=back_button(lang=settings.lang),
        )
        return

    await state.update_data(url=url)
    await state.set_state(CalendarLinkingStates.waiting_for_calendar_name)
    await edit_message(
        message.bot,
        message.chat.id,
        last_message_id,
        state,
        text=(
            f"{t('calendar.new.title', lang=settings.lang)}\n\n{t('calendar.link.enter_name', lang=settings.lang)}\n\n"
        ),
        parse_mode="HTML",
        reply_markup=back_button(lang=settings.lang),
    )


@router.message(StateFilter(CalendarLinkingStates.waiting_for_calendar_name))
async def process_calendar_name(message: Message, state: FSMContext, settings: SettingsData) -> None:
    """Process calendar name."""
    last_message_id = await get_last_message_id(state)
    if last_message_id is None:
        logger.error("Last message id is not found", extra={"state": state})
        return

    name = message.text
    await message.delete()

    if name is None or len(name) == 0:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            text=(
                f"{t('calendar.new.title', lang=settings.lang)}\n\n"
                f"{t('calendar.link.name.empty', lang=settings.lang)}\n\n"
            ),
            parse_mode="HTML",
            reply_markup=back_button(lang=settings.lang),
        )
        return

    if len(name) > 255:
        await edit_message(
            message.bot,
            message.chat.id,
            last_message_id,
            state,
            text=(
                f"{t('calendar.new.title', lang=settings.lang)}\n\n"
                f"{t('calendar.link.name.too.long', lang=settings.lang)}\n\n"
            ),
            parse_mode="HTML",
            reply_markup=back_button(lang=settings.lang),
        )
        return

    await state.update_data(name=name)
    await state.set_state(CalendarLinkingStates.waiting_for_calendar_confirmation)
    data = await state.get_data()
    url: str | None = data.get("url")
    await edit_message(
        message.bot,
        message.chat.id,
        last_message_id,
        state,
        text=(
            f"{t('calendar.new.title', lang=settings.lang)}\n\n"
            f"{t('calendar.link.confirm.message', lang=settings.lang, name=name, link=url)}\n\n"
        ),
        parse_mode="HTML",
        reply_markup=confirm_calendar_inline(lang=settings.lang),
    )


@router.callback_query(
    F.data == "calendar_confirm", StateFilter(CalendarLinkingStates.waiting_for_calendar_confirmation)
)
async def calendar_confirm(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Confirm calendar linking."""

    # Get data from state
    state_data = await state.get_data()
    url: str | None = state_data.get("url")
    name: str | None = state_data.get("name")

    # Get user_id
    user_id = query.from_user.id
    logger.debug("Calendar confirm: user_id", extra={"user_id": user_id})
    # Upload calendar if we have all required data
    if url and name:
        try:
            await store.UploadService.upload_ical_url(user_id, name, url)
            logger.info(f"User {user_id} successfully linked calendar: {name} ({url})")
        except Exception as e:
            logger.error(f"Error uploading calendar for user {user_id}: {e}", exc_info=e)
            await edit_message(
                query.bot,
                query.message.chat.id,
                query.message.message_id,
                state,
                text=(
                    f"{t('calendar.new.title', lang=settings.lang)}\n\n"
                    f"{t('calendar.link.error', lang=settings.lang)}\n\n"
                ),
                parse_mode="HTML",
                reply_markup=back_button("menu_link_calendar", lang=settings.lang),
            )
            return

    await state.set_state(CalendarLinkingStates.in_calendar_menu)
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=t("calendar.link.success", lang=settings.lang),
        parse_mode="HTML",
        reply_markup=back_button("menu_link_calendar", lang=settings.lang),
    )


@router.callback_query(F.data.startswith("calendar_rename:"), StateFilter(CalendarLinkingStates.in_calendar_menu))
async def calendar_rename(query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData) -> None:
    """Rename a calendar."""
    if query.data is None or len(query.data) == 0:
        logger.error("Query data is None or empty", extra={"query": query})
        return

    calendar_id = int(query.data.split(":")[1])

    calendar = await store.CalendarService.get_by_id(calendar_id)
    if calendar is None:
        logger.error("Calendar is not found", extra={"calendar_id": calendar_id})
        return

    await clean_messages(query.bot, query.message.chat.id, state)

    await state.set_state(CalendarLinkingStates.waiting_for_calendar_name_rename)

    last_message_id = await get_last_message_id(state)
    if last_message_id is None:
        logger.error("Last message id is not found", extra={"state": state})
        return

    text = (
        f"{t('calendar.rename.title', old_name=calendar.name, lang=settings.lang)}\n\n"
        f"{t('calendar.rename.enter.new.name', lang=settings.lang)}\n\n"
    )

    await state.update_data(calendar_id=calendar_id)

    await edit_message(
        query.bot,
        calendar.user_id,
        last_message_id,
        state,
        text=text,
        parse_mode="HTML",
        reply_markup=back_button(lang=settings.lang),
    )


@router.message(StateFilter(CalendarLinkingStates.waiting_for_calendar_name_rename))
async def process_calendar_name_rename(
    message: Message, state: FSMContext, store: Store, settings: SettingsData
) -> None:
    """Process calendar name rename."""
    last_message_id = await get_last_message_id(state)
    if last_message_id is None:
        logger.error("Last message id is not found", extra={"state": state})
        return

    data = await state.get_data()
    calendar_id = data.get("calendar_id")
    if calendar_id is None:
        logger.error("Calendar id is not found", extra={"state": state})
        return
    calendar = await store.CalendarService.get_by_id(calendar_id)
    if calendar is None:
        logger.error("Calendar is not found", extra={"calendar_id": calendar_id})
        return

    name = message.text
    await message.delete()

    if name is None or len(name) == 0:
        await edit_message(
            message.bot,
            calendar.user_id,
            last_message_id,
            state,
            text=(
                f"{t('calendar.rename.title', old_name=calendar.name, lang=settings.lang)}\n\n"
                f"{t('calendar.rename.name.empty', lang=settings.lang)}\n\n"
            ),
            parse_mode="HTML",
            reply_markup=back_button(lang=settings.lang),
        )
        return

    if len(name) > 255:
        await edit_message(
            message.bot,
            calendar.user_id,
            last_message_id,
            state,
            text=(
                f"{t('calendar.new.title', lang=settings.lang)}\n\n"
                f"{t('calendar.link.name.too.long', lang=settings.lang)}\n\n"
            ),
            parse_mode="HTML",
            reply_markup=back_button(lang=settings.lang),
        )
        return

    await state.update_data(name=name)
    await state.set_state(CalendarLinkingStates.waiting_for_calendar_confirmation)
    await edit_message(
        message.bot,
        calendar.user_id,
        last_message_id,
        state,
        text=(
            f"{t('calendar.rename.title', old_name=calendar.name, lang=settings.lang)}\n\n"
            f"{t('calendar.rename.confirm.message', lang=settings.lang, name=name)}\n\n"
        ),
        parse_mode="HTML",
        reply_markup=confirm_calendar_rename_inline(lang=settings.lang),
        extra_data={"calendar_id": calendar_id, "new_name": name},
    )


@router.callback_query(
    F.data == "calendar_rename_confirm", StateFilter(CalendarLinkingStates.waiting_for_calendar_confirmation)
)
async def calendar_rename_confirm(
    query: CallbackQuery, state: FSMContext, store: Store, settings: SettingsData
) -> None:
    """Confirm calendar rename."""
    data = await state.get_data()
    calendar_id = data.get("calendar_id")
    if calendar_id is None:
        logger.error("Calendar id is not found", extra={"state": state})
        return
    name = data.get("name")
    if name is None:
        logger.error("New name is not found", extra={"state": state})
        return
    await store.CalendarService.update(calendar_id, CalendarUpdateSchema(name=name))
    await state.set_state(CalendarLinkingStates.in_calendar_menu)
    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=t("calendar.rename.success", lang=settings.lang),
        parse_mode="HTML",
        reply_markup=back_button("menu_link_calendar", lang=settings.lang),
    )
