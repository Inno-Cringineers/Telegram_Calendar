from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard():
    """Main menu with basic actions."""
    buttons = [
        [KeyboardButton(text="📅 Мои события")],
        [KeyboardButton(text="➕ Новое событие")],
        [KeyboardButton(text="⚙️ Настройки")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие...",
    )


def get_confirmation_keyboard():
    """Simple yes/no confirmation."""
    buttons = [
        [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Ответьте...",
    )


def get_skip_keyboard():
    """Keyboard with skip option."""
    buttons = [
        [KeyboardButton(text="⏭️ Пропустить")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def get_event_confirmation_inline():
    """Inline keyboard for event confirmation."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_event"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_create"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_event_actions_inline(event_id: int):
    """Inline keyboard for event actions."""
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_event_{event_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_event_{event_id}"),
        ],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_confirmation_inline(event_id: int):
    """Inline keyboard for delete confirmation."""
    buttons = [
        [
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"confirm_delete_{event_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
