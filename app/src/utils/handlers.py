from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta, timezone

from aiogram.client.bot import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from logger.logger import logger


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


def is_valid_query(query: CallbackQuery) -> bool:
    if query.message is None or not isinstance(query.message, Message):
        logger.error("Query message is None or not a Message", extra={"query": query})
        return False

    if query.bot is None:
        logger.error("Query bot is None", extra={"query": query})
        return False

    return True


async def send_message(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    text: str,
    reply_markup=None,
    parse_mode: str = "HTML",
    delete_keyboard: bool = False,
    delete_message: bool = False,
    extra_data: dict | None = None,
):
    """Send message to chat. Used to clean up messages after state is cleared."""

    new_message = await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup)
    if not isinstance(new_message, Message):
        raise ValueError(f"New message is not a Message, bot returned {new_message}")

    data = await state.get_data()
    sent = data.get("sent_messages", [])
    sent.append(
        {
            "message_id": new_message.message_id,
            "delete_keyboard": delete_keyboard,
            "delete_message": delete_message,
            "extra_data": extra_data,
            "text": text,
        }
    )
    await state.update_data(sent_messages=sent)

    await state.update_data(last_message=new_message.message_id)
    logger.debug(f"Sent message {new_message.message_id} to {chat_id}")
    logger.debug(f"Sent messages: {sent}")


async def get_last_message_id(state: FSMContext) -> int | None:
    """Get last message from state. Used to clean up messages after state is cleared."""
    data = await state.get_data()
    return data.get("last_message", None)


async def edit_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    state: FSMContext,
    text: str,
    reply_markup=None,
    parse_mode: str = "HTML",
    delete_keyboard: bool | None = None,
    delete_message: bool | None = None,
    extra_data: dict | None = None,
):
    """Edit message in chat. Used to clean up messages after state is cleared."""

    new_message = await bot.edit_message_text(
        chat_id=chat_id, message_id=message_id, text=text, parse_mode=parse_mode, reply_markup=reply_markup
    )
    if not isinstance(new_message, Message):
        raise ValueError(f"New message is not a Message, bot returned {new_message}")

    data = await state.get_data()
    is_in_sent = False
    sent = data.get("sent_messages", [])
    for msg in sent:
        if msg["message_id"] == message_id:
            msg["message_id"] = new_message.message_id
            msg["delete_keyboard"] = delete_keyboard if delete_keyboard is not None else msg["delete_keyboard"]
            msg["delete_message"] = delete_message if delete_message is not None else msg["delete_message"]
            msg["extra_data"] = extra_data if extra_data is not None else msg["extra_data"]
            msg["text"] = text
            is_in_sent = True
            await state.update_data(sent_messages=sent)

    if not is_in_sent:
        sent.append(
            {
                "message_id": new_message.message_id,
                "delete_keyboard": delete_keyboard if delete_keyboard is not None else False,
                "delete_message": delete_message if delete_message is not None else False,
                "extra_data": extra_data if extra_data is not None else None,
                "text": text,
            }
        )

    await state.update_data(last_message=new_message.message_id)
    logger.debug(f"Edited message {new_message.message_id} to {text}")
    logger.debug(f"Edited messages: {sent}")


async def clean_messages(bot: Bot, chat_id: int, state: FSMContext, delete_all: bool = False):
    """Clean up messages from chat. Used to clean up messages after state is cleared."""
    data = await state.get_data()
    sent = data.get("sent_messages", [])
    removed = []
    for msg in sent:
        logger.debug(f"Cleaning message {msg['message_id']}")
        if msg["delete_message"] is True or delete_all is True:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=msg["message_id"])
                logger.debug(f"Deleted message {msg['message_id']}")
                removed.append(msg)
            except Exception as e:
                logger.error(f"Error deleting message {msg['message_id']}: {e}")
            continue
        if msg["delete_keyboard"] is True:
            try:
                await bot.edit_message_reply_markup(chat_id=chat_id, message_id=msg["message_id"], reply_markup=None)
                logger.debug(f"Deleted keyboard for message {msg['message_id']}")
                removed.append(msg)
            except Exception as e:
                logger.error(f"Error deleting keyboard for message {msg['message_id']}: {e}")

    for msg in removed:
        sent.remove(msg)

    await state.update_data(sent_messages=sent)


async def get_messages(state: FSMContext) -> list[dict]:
    """Get messages from state."""
    data = await state.get_data()
    return data.get("sent_messages", [])


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
