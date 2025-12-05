from datetime import UTC, datetime, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from logger.logger import logger
from repositories.schemas import EventDurationFilter
from store.store import Store

router = Router()


@router.callback_query(F.data == "menu_daily_plan")
async def get_daily_plan(query: CallbackQuery, state: FSMContext, store: Store, lang: str) -> None:
    """Send daily plan to user."""
    user_id = query.from_user.id

    # todays 00:00
    from_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    # tomorrow 00:00
    to_date = from_date + timedelta(days=1)

    events = await store.EventService.get_events_in_range(
        EventDurationFilter(user_id=user_id, duration_from=from_date, duration_to=to_date)
    )
    logger.debug(f"events: {events}")
