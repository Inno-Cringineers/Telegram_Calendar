from datetime import UTC, datetime, timedelta, timezone

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from i18n.strings import t
from keyboards.inline import back_button
from repositories.schemas import EventDurationFilter, EventResponse
from store.store import Store
from utils.handlers import edit_message, send_message

router = Router()


def parse_user_timezone(tz_str: str) -> timezone:
    """
    Convert strings like 'UTC+3', 'UTC+5:30', 'UTC-4:45' -> timezone object.
    """
    if not tz_str.startswith("UTC"):
        raise ValueError("Invalid timezone format")

    if tz_str == "UTC":
        return UTC

    sign = 1 if "+" in tz_str else -1
    _, offset_str = tz_str.split("UTC")[1].split(sign == 1 and "+" or "-")

    if ":" in offset_str:
        hours, minutes = map(int, offset_str.split(":"))
    else:
        hours, minutes = int(offset_str), 0

    return timezone(timedelta(hours=sign * hours, minutes=sign * minutes))


@router.callback_query(F.data == "menu_daily_plan")
async def get_daily_plan(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Send daily plan to user."""
    user_id = query.from_user.id

    settings = await store.SettingsService.get_by_user_id(user_id)
    user_tz = parse_user_timezone(settings.timezone)

    now_local = datetime.now(user_tz)

    local_from = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    local_to = local_from + timedelta(days=1)

    utc_from = local_from.astimezone(UTC)
    utc_to = local_to.astimezone(UTC)

    events = await store.EventService.get_events_in_range(
        EventDurationFilter(user_id=user_id, duration_from=utc_from, duration_to=utc_to)
    )
    if events == []:
        await edit_message(
            query.bot,
            query.message.chat.id,
            query.message.message_id,
            state,
            text=f"{t('daily.plan.title', lang=lang, today=now_local.strftime('%d.%m.%Y'))}\n\n{t('daily.plan.no.events', lang=lang)}",
            reply_markup=back_button("back_to_main", lang=lang),
            parse_mode="HTML",
            delete_keyboard=True,
        )
        return

    await edit_message(
        query.bot,
        query.message.chat.id,
        query.message.message_id,
        state,
        text=t("daily.plan.title", lang=lang, today=now_local.strftime("%d.%m.%Y")),
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
                "daily.plan.event.content",
                lang=lang,
                title=event.title or t("daily.plan.event.title.none", lang=lang),
                description=event.description or t("daily.plan.event.description.none", lang=lang),
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
        t("daily.plan.end", lang=lang),
        reply_markup=back_button("back_to_main", lang=lang),
        parse_mode="HTML",
        delete_keyboard=True,
        delete_message=False,
    )


def get_event_duration(event: EventResponse, tz_info: timezone, lang: str) -> str:
    if event.all_day:
        return t("daily.plan.event.duration.all.day", lang=lang)

    start = event.date_start.astimezone(tz_info).strftime("%H:%M")
    end = event.date_end.astimezone(tz_info).strftime("%H:%M")

    return t(
        "daily.plan.event.duration.not.all.day",
        lang=lang,
        start=start,
        end=end,
    )


async def get_event_source(event: EventResponse, store: Store, lang: str) -> str:
    calendar = await store.CalendarService.get_by_id(event.calendar_id)
    if calendar.url is not None:
        return t("daily.plan.event.source.external", lang=lang, name=calendar.name, link=calendar.url)
    return t("daily.plan.event.source.local", lang=lang)
