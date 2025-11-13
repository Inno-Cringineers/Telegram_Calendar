from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from datetime import datetime

from bot.states.event import CreateEventStates
from bot.keyboards.reply import (
    get_confirmation_keyboard,
    get_event_confirmation_inline,
)
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


@router.message(Command("new"))
async def start_create_event(message: Message, state: FSMContext):
    """Start event creation flow."""
    logger.info(f"User {message.from_user.id} started creating event")
    
    await state.set_state(CreateEventStates.waiting_for_title)
    await message.answer(
        "📝 Введите название события:\n\n"
        "(Максимум 100 символов)"
    )


@router.message(CreateEventStates.waiting_for_title)
async def process_event_title(message: Message, state: FSMContext):
    """Process event title."""
    title = message.text.strip()
    
    if len(title) == 0:
        await message.answer("❌ Название не может быть пустым")
        return
    
    if len(title) > 100:
        await message.answer("❌ Название слишком длинное (максимум 100 символов)")
        return
    
    await state.update_data(title=title)
    await state.set_state(CreateEventStates.waiting_for_description)
    await message.answer(
        "📄 Введите описание события:\n\n"
        "(или напишите 'Пропустить' чтобы пропустить)"
    )


@router.message(CreateEventStates.waiting_for_description)
async def process_event_description(message: Message, state: FSMContext):
    """Process event description."""
    description = "" if message.text.lower() in ["пропустить", "/skip"] else message.text.strip()
    
    await state.update_data(description=description)
    await state.set_state(CreateEventStates.waiting_for_date)
    await message.answer(
        "📅 Введите дату события:\n\n"
        "Формат: ДД.ММ.YYYY (например: 25.12.2024)"
    )


@router.message(CreateEventStates.waiting_for_date)
async def process_event_date(message: Message, state: FSMContext):
    """Process event date with validation."""
    date_str = message.text.strip()
    
    if not is_valid_date(date_str):
        await message.answer(
            "❌ Неверный формат даты или дата в прошлом\n\n"
            "Используйте формат: ДД.ММ.YYYY (например: 25.12.2024)"
        )
        return
    
    await state.update_data(date=date_str)
    await state.set_state(CreateEventStates.waiting_for_time)
    await message.answer(
        "⏰ Введите время события:\n\n"
        "Формат: ЧЧ:ММ (например: 14:30)"
    )


@router.message(CreateEventStates.waiting_for_time)
async def process_event_time(message: Message, state: FSMContext):
    """Process event time with validation."""
    time_str = message.text.strip()
    
    if not is_valid_time(time_str):
        await message.answer(
            "❌ Неверный формат времени\n\n"
            "Используйте формат: ЧЧ:ММ (например: 14:30)"
        )
        return
    
    data = await state.get_data()
    await state.update_data(time=time_str)
    
    # Show preview of the event
    preview_text = f"""
📋 Проверьте данные события:

📝 <b>Название:</b> {data['title']}
📄 <b>Описание:</b> {data['description'] if data['description'] else '(не указано)'}
📅 <b>Дата:</b> {data['date']}
⏰ <b>Время:</b> {time_str}

✅ Все верно?
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
        f"title={data['title']}, date={data['date']}, time={data['time']}"
    )
    
    # TODO: Save event to database
    # await save_event(user_id, data)
    
    await query.answer("✅ Событие создано!")
    await query.message.edit_text(
        "✅ <b>Событие успешно добавлено в календарь</b>",
        parse_mode="HTML",
    )
    await state.clear()


@router.callback_query(F.data == "cancel_create")
async def cancel_create_event(query: CallbackQuery, state: FSMContext):
    """Cancel event creation."""
    logger.info(f"User {query.from_user.id} cancelled event creation")
    
    await query.answer("❌ Создание события отменено")
    await query.message.edit_text("❌ <b>Операция отменена</b>", parse_mode="HTML")
    await state.clear()
