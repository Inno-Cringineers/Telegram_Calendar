from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.states.states import EventsMenuStates
from bot.states.states import CreateEventStates
from bot.keyboards.inline import *
from bot.logger import logger

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
async def process_create_new_event_callback(query: CallbackQuery, state: FSMContext):
    """Transition beetween states."""
    user_name = query.from_user.first_name
    user_id = query.from_user.id
    logger.info(f"User {user_name} (ID: {user_id}) creating event")

    await state.set_state(CreateEventStates.waiting_for_title)

    await query.message.edit_text(
        "📝 Enter event title:\n\n",
        reply_markup=get_cancel_keyboard("events_cancel")
    )

@router.callback_query(F.data == "events_cancel", StateFilter(CreateEventStates))
async def cancel_event_creation(query: CallbackQuery, state: FSMContext):
    """Cancel event creation."""
    await state.clear()
    await query.message.edit_text(
        "❌ Event creation cancelled",
        reply_markup=get_back_button("menu_events")
    )

@router.message(CreateEventStates.waiting_for_title)
async def process_event_title(message: Message, state: FSMContext):
    """Process event title."""
    title = message.text
    if title is None or len(title) == 0:
        await message.answer("❌ Title shouldnt be empty")
        return
    
    if len(title) > 100:
        await message.answer("❌ Title too long (maximum 100 chars)")
        return
    
    await state.update_data(title=title)
    await state.set_state(CreateEventStates.waiting_for_description)


    await message.answer(
        "📄 Enter description:\n\n",
        reply_markup=get_skip_keyboard(skip_callback="skip_description", cancel_callback="events_cancel")
    )


@router.message(CreateEventStates.waiting_for_description)
async def process_event_description(message: Message, state: FSMContext):
    """Process event description."""
    description = message.text
    
    await state.update_data(description=description)

    await state.set_state(CreateEventStates.waiting_for_start_date)
    await message.answer(
        "📅 Enter start date:\n\n"
        "Format: DD.MM.YYYY (example: 25.12.2025)",
        reply_markup=get_cancel_keyboard("events_cancel")
    )

@router.callback_query(F.data == "skip_description", CreateEventStates.waiting_for_description)
async def skip_event_description(query: CallbackQuery, state: FSMContext):
    """Skip event description step."""
    await state.update_data(description=None)
    await state.set_state(CreateEventStates.waiting_for_start_date)

    await query.message.edit_text(
        "📅 Enter start date:\n\n"
        "Format: DD.MM.YYYY (example: 25.12.2025)",
        reply_markup=get_cancel_keyboard("events_cancel")
    )

@router.message(CreateEventStates.waiting_for_start_date)
async def process_event_date(message: Message, state: FSMContext):
    """Process event date with validation."""
    date_str = message.text.strip()
    
    if not is_valid_date(date_str):
        await message.answer(
            "❌ Incorrect date format\n\n"
            "Format: DD.MM.YYYY (example: 25.12.2025)",
            reply_markup=get_cancel_keyboard("events_cancel")
        )
        return
    
    await state.update_data(start_date=date_str)
    await state.set_state(CreateEventStates.waiting_for_start_time)
    await message.answer(
        "⏰ Enter start time:\n\n"
        "Format: HH:MM (example: 14:30)",
        reply_markup=get_cancel_keyboard("events_cancel")
    )


@router.message(CreateEventStates.waiting_for_start_time)
async def process_event_time(message: Message, state: FSMContext):
    """Process event time with validation."""
    time_str = message.text.strip()
    
    if not is_valid_time(time_str):
        await message.answer(
            "❌ Incorrect time format\n\n"
            "Use format: HH:MM (example: 14:30)"
        )
        return
    
    data = await state.get_data()
    await state.update_data(start_time=time_str)
    
    # Show preview of the event
    preview_text = f"""
📋 Check event data:

📝 <b>Title:</b> {data['title']}
📄 <b>description:</b> {data['description'] if data['description'] else '(None)'}
📅 <b>Start date:</b> {data['start_date']}
⏰ <b>Start time:</b> {time_str}

✅ All right?
    """.strip()
    
    await state.set_state(CreateEventStates.waiting_for_confirmation)
    await message.answer(
        preview_text,
        parse_mode="HTML",
        reply_markup=get_event_confirmation_inline(),
    )


@router.callback_query(F.data == "confirm_event", CreateEventStates.waiting_for_confirmation)
async def confirm_event(query: CallbackQuery, state: FSMContext):
    """Confirm and save event."""
    data = await state.get_data()
    user_id = query.from_user.id
    
    logger.info(
        f"User {user_id} confirmed event creation: "
        f"title={data['title']}, date={data['start_date']}, time={data['start_time']}"
    )
    
    # TODO: Save event to database
    # await save_event(user_id, data)
    
    await query.answer("✅ Event created!")
    await query.message.edit_text(
        "✅ <b>Event successfully created</b>",
        parse_mode="HTML",
        reply_markup=get_back_button("menu_events"),
    )
    await state.clear()
