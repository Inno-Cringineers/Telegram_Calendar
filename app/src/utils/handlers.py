from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, time

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from logger.logger import logger


async def save_bot_message(state: FSMContext, msg: Message):
    """Save bot message to state. Used to clean up messages after state is cleared.

    Args:
        state: FSMContext instance.
        msg: Message instance.
    """
    data = await state.get_data()
    sent = data.get("sent_messages", [])
    sent.append(msg.message_id)
    await state.update_data(sent_messages=sent)
    await state.update_data(last_message=msg)


async def remove_old_keyboards(bot: Bot, state: FSMContext, chat_id: int):
    """Remove old keyboards from chat. Used to clean up messages after state is cleared."""
    data = await state.get_data()
    sent = data.get("sent_messages", [])

    for msg_id in sent:
        try:
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg_id, reply_markup=None)
        except Exception:
            logger.error(f"Error removing message reply markup: {msg_id} from chat {chat_id}")
            continue

    await state.update_data(sent_messages=[])


async def send_clean_message(
    message: Message, state: FSMContext, text: str, reply_markup=None, parse_mode: str = "HTML"
):
    """Send clean message to chat. Used to clean up messages after state is cleared."""
    if message.bot is None:
        raise ValueError("Bot is not set")

    await remove_old_keyboards(message.bot, state, message.chat.id)

    new_msg = await message.answer(text, parse_mode=parse_mode, reply_markup=reply_markup)
    await save_bot_message(state, new_msg)

    return new_msg


async def get_last_message(state: FSMContext) -> Message:
    """Get last bot message from state."""
    data = await state.get_data()
    last_message = data.get("last_message")
    if not last_message:
        raise ValueError("No messages sent")

    return last_message


async def edit_message(
    message: Message, state: FSMContext, text: str, reply_markup=None, parse_mode: str = "HTML"
) -> None:
    """Edit last bot message in chat."""
    if message.bot is None:
        raise ValueError("Bot is not set")
    await message.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    await save_bot_message(state, message)


def log_action(action: str) -> Callable:
    """Decorator to log router actions with user id when available."""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            """Try to extract CallbackQuery or Message to log user id."""
            user_id = None
            for a in args:
                if isinstance(a, CallbackQuery) or isinstance(a, Message):
                    user_id = a.from_user.id if a.from_user else None
                    break
            if user_id is not None:
                logger.info(f"User {user_id}: {action}")
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def is_valid_time_hhmm(value: str) -> bool:
    """Validate time string in HH:MM (24-hour) format.


    Accepts leading zeros (e.g., '09:05').
    """
    if not isinstance(value, str):
        return False

    parts = value.split(":")
    if len(parts) != 2:
        return False
    for part in parts:
        if not part.isdigit() or len(part) != 2:
            return False

    hour, minute = parts
    if not (hour.isdigit() and minute.isdigit()):
        return False

    try:
        h = int(hour)
        m = int(minute)
    except ValueError:
        return False

    return 0 <= h <= 23 and 0 <= m <= 59


def _time_to_minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def detect_timezone_from_local_time(user_time_str: str, reference: datetime | None = None) -> str:
    """Detect timezone string like 'UTC+3', 'UTC-5:30', 'UTC+5:45' from user's local time.


    Args:
    user_time_str: user-provided time in HH:MM (24-hour).
    reference: optional reference datetime in UTC (for testing). If None uses now UTC.


    Returns:
    Formatted timezone string (e.g. 'UTC', 'UTC+3', 'UTC-4:30').


    Notes:
    - This function assumes the user provided their **current** local time.
    - It computes the difference between that local time and current UTC time and
    converts it to the nearest 15-minute increment (common TZ offsets).
    - If the offset is exactly 0 -> 'UTC'.
    """
    if not is_valid_time_hhmm(user_time_str):
        raise ValueError("user_time_str must be in HH:MM format")

    user_hour, user_minute = (int(p) for p in user_time_str.split(":"))
    user_time = time(hour=user_hour, minute=user_minute)

    ref = reference or datetime.now(UTC)
    utc_time = ref.timetz()

    user_minutes = _time_to_minutes(user_time)
    utc_minutes = _time_to_minutes(utc_time)

    # compute raw difference (user - utc)
    diff_minutes = user_minutes - utc_minutes

    # handle wrap-around across midnight
    if diff_minutes <= -12 * 60:
        diff_minutes += 24 * 60
    elif diff_minutes > 12 * 60:
        diff_minutes -= 24 * 60

    # Round to nearest 15 minutes (most timezones are multiples of 15 minutes)
    remainder = diff_minutes % 15
    if remainder >= 8:
        diff_minutes += 15 - remainder
    else:
        diff_minutes -= remainder

    sign = "+" if diff_minutes >= 0 else "-"
    abs_minutes = abs(diff_minutes)
    hours = abs_minutes // 60
    minutes = abs_minutes % 60

    if hours == 0 and minutes == 0:
        return "UTC"

    if minutes == 0:
        return f"UTC{sign}{hours}"
    else:
        return f"UTC{sign}{hours}:{str(minutes).zfill(2)}"
