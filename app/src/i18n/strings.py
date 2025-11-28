"""Localization strings for user-facing text.

All user-facing strings are stored here with English and Russian translations.
"""

# TODO: Check babel format for translations

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # Start handler
        "start.welcome": "👋 <b>Welcome to the Telegram Calendar reminder, {user_name}!</b>\n\nI can help you manage your events and reminders, including from external calendars.\n\n📋 <b>Commands:</b>\n/start - Show this dialog\n/help - Get help\n/menu - Open main menu\n\n🎯 <b>Main functions:</b>\n• 📅 Viewing events \n• ➕ Creating events\n• ✏️ Editing events\n• 🗑️ Deleting events\n• 🔗 Importing external calendars (google, outlook, etc.)\n• 📤 Exporting events\n• ⏰ Reminders for events \n• 📋 Daily plans",  # noqa: E501
        # Menu
        "menu.main.title": "🏠 <b>Main Menu</b>\n\nChoose an option:",
        "menu.updated": "Menu updated",
        # Settings
        "settings.title": "⚙️ <b>Settings</b>\n\nChoose a setting to modify:",
        "settings.timezone.selected": "✅ Timezone setting selected",
        "settings.timezone.title": "🌍 Timezone",
        "settings.timezone.current": "Current timezone: UTC+2 (Mocked)",
        "settings.timezone.select": "Select timezone:",
        "settings.timezone.feature_dev": "Feature is under development.",
        "settings.language.selected": "✅ Language setting selected",
        "settings.language.title": "🇬🇧 <b>Language</b>",
        "settings.language.current": "Current language: English (Mocked)",
        "settings.language.available": "Feature is under development. Available languages: English, Русский",
        "settings.quiet_hours.selected": "✅ Quiet hours setting selected",
        "settings.quiet_hours.title": "🔇 <b>Quiet Hours</b>",
        "settings.quiet_hours.current": "Current quiet hours: 22:00 - 08:00 (Mocked)",
        "settings.quiet_hours.description": "Feature is under development. No notifications will be sent during quiet hours.",  # noqa: E501
        "settings.daily_plans_time.selected": "✅ Daily plans time setting selected",
        "settings.daily_plans_time.title": "⏰ <b>Daily plans Time</b>",
        "settings.daily_plans_time.current": "Current time: 09:00 (Mocked)",
        "settings.daily_plans_time.description": "Feature is under development. Daily plan will be sent at this time every day.",  # noqa: E501
        # Events
        "events.title": "📅 <b>Events</b>\n\nChoose an events option:",
        "events.import.selected": "📥 Event import selected",
        "events.import.title": "📥 <b>Events import</b>",
        "events.import.description": "Please load file in .ics format to the chat",
        "events.export.selected": "📥 Event export selected",
        "events.export.title": "📥 <b>Events export</b>",
        "events.export.description": "Your events exported in .ics format (only internal events)",
        "events.create.selected": "➕ Event creation selected",
        "events.create.title": "➕ <b>Events creation</b>",
        "events.view.selected": "🔍 Events viewing selected",
        "events.view.title": "🔍 <b>Events viewing</b>",
        "events.feature_dev": "Feature is under development.",
        # Create event
        "create_event.enter_title": "📝 Enter event title:\n\n",
        "create_event.cancelled": "❌ Event creation cancelled",
        "create_event.title_empty": "❌ Title should not be empty",
        "create_event.title_too_long": "❌ Title too long (maximum 100 chars)",
        "create_event.enter_description": "📄 Enter description:\n\n",
        "create_event.enter_date": "📅 Enter start date:\n\nFormat: DD.MM.YYYY (example: 25.12.2025)",
        "create_event.date_format_error": "❌ Incorrect date format\n\nFormat: DD.MM.YYYY (example: 25.12.2025)",
        "create_event.enter_time": "⏰ Enter start time:\n\nFormat: HH:MM (example: 14:30)",
        "create_event.time_format_error": "❌ Incorrect time format\n\nUse format: HH:MM (example: 14:30)",
        "create_event.preview.title": "📋 Check event data:",
        "create_event.preview.title_label": "📝 <b>Title:</b> {title}",
        "create_event.preview.description_label": "📄 <b>Description:</b> {description}",
        "create_event.preview.date_label": "📅 <b>Start date:</b> {date}",
        "create_event.preview.time_label": "⏰ <b>Start time:</b> {time}",
        "create_event.preview.confirm": "✅ All right?",
        "create_event.preview.description_none": "(None)",
        "create_event.confirmed": "✅ Event created!",
        "create_event.success": "✅ <b>Event successfully created</b>",
        # Calendar
        "calendar.link.title": "🔗 <b>Link a Calendar</b>\n\nChoose an action:",
        "calendar.list.answer": "📑 Your calendars",
        "calendar.list.title": "📑 <b>Your Calendars</b>",
        "calendar.list.linked": "<b>Linked Calendars:</b>",
        "calendar.list.feature_dev": "Feature is under development. You can unlink calendars here.",
        "calendar.new.answer": "🔗 Link new calendar",
        "calendar.new.title": "🔗 <b>Link a New Calendar</b>",
        "calendar.new.enter_link": "<b>Enter the ical link:</b>",
        # Daily plan
        "daily_plan.generating": "📋 Generating daily plan...",
        "daily_plan.end": "End of daily plan",
        # Buttons - Main menu
        "btn.settings": "⚙️ Settings",
        "btn.events": "📅 Events",
        "btn.daily_plan": "📋 Get Daily Plan",
        "btn.external_calendars": "🔗 External calendars",
        "btn.back": "« Back",
        # Buttons - Settings
        "btn.timezone": "🌍 Timezone",
        "btn.language": "🇬🇧 Language",
        "btn.quiet_hours": "🔇 Quiet Hours",
        "btn.daily_plans_time": "⏰ Daily Plans Time",
        # Buttons - Events
        "btn.import": "📥 Import",
        "btn.export": "📤 Export",
        "btn.add": "➕ Add",
        "btn.view": "🔍 View",
        "btn.create_by_dialog": "📅 Create by dialog",
        # Buttons - Calendar
        "btn.calendar_list": "📑 List of Calendars",
        "btn.link_calendar": "🔗 Link a New Calendar",
        # Buttons - Language
        "btn.language.en": "English",
        "btn.language.ru": "Русский",
        # Buttons - Quiet hours
        "btn.quiet_hours.enter": "enter quiet hours",
        # Buttons - Daily plan time
        "btn.daily_plan_time.enter": "enter daily plans time",
        # Buttons - Actions
        "btn.cancel": "❌ Cancel",
        "btn.skip": "⏭ Skip",
        "btn.accept": "✅ Accept",
        "btn.reject": "❌ Reject",
        "btn.delete": "❌ Delete",
        "btn.edit": "✏️ Edit",
        # Calendar widget
        "calendar.prev_month": "<<",
        "calendar.next_month": ">>",
        "calendar.weekdays": "Mon,Tue,Wed,Thu,Fri,Sat,Sun",
    },
    "ru": {
        # Start handler
        "start.welcome": "👋 <b>Добро пожаловать в Telegram Calendar reminder, {user_name}!</b>\n\nЯ могу помочь управлять вашими событиями и напоминаниями, даже из внешних календарей.\n\n📋 <b>Команды:</b>\n/start - Показать это диалоговое окно\n/help - Получить помощь\n/menu - Открыть главное меню\n\n🎯 <b>Основные функции:</b>\n• 📅 Просмотр событий\n• ➕ Создание событий\n• ✏️ Редактирование событий\n• 🗑️ Удаление событий\n• 🔗 Экспорт внешних календарей (google, outlook и т.д.)\n• ⏰ Напоминания о событиях\n• 📋 Ежедневные планы",  # noqa: E501
        # Menu
        "menu.main.title": "🏠 <b>Главное меню</b>\n\nВыберите опцию:",
        "menu.updated": "Меню обновлено",
        # Settings
        "settings.title": "⚙️ <b>Настройки</b>\n\nВыберите настройку для изменения:",
        "settings.timezone.selected": "✅ Настройка часового пояса выбрана",
        "settings.timezone.title": "🌍 Часовой пояс",
        "settings.timezone.current": "Текущий часовой пояс: UTC+2 (Заглушка)",
        "settings.timezone.select": "Выберите часовой пояс:",
        "settings.timezone.feature_dev": "Функция находится в разработке.",
        "settings.language.selected": "✅ Настройка языка выбрана",
        "settings.language.title": "🇬🇧 <b>Язык</b>",
        "settings.language.current": "Текущий язык: Русский (Заглушка)",
        "settings.language.available": "Функция находится в разработке. Доступные языки: English, Русский",
        "settings.quiet_hours.selected": "✅ Настройка тихих часов выбрана",
        "settings.quiet_hours.title": "🔇 <b>Тихие часы</b>",
        "settings.quiet_hours.current": "Текущие тихие часы: 22:00 - 08:00 (Заглушка)",
        "settings.quiet_hours.description": "Функция находится в разработке. Уведомления не будут отправляться в тихие часы.",  # noqa: E501
        "settings.daily_plans_time.selected": "✅ Настройка времени ежедневных планов выбрана",
        "settings.daily_plans_time.title": "⏰ <b>Время ежедневных планов</b>",
        "settings.daily_plans_time.current": "Текущее время: 09:00 (Заглушка)",
        "settings.daily_plans_time.description": "Функция находится в разработке. Ежедневный план будет отправляться в это время каждый день.",  # noqa: E501
        # Events
        "events.title": "📅 <b>События</b>\n\nВыберите опцию событий:",
        "events.import.selected": "📥 Импорт событий выбран",
        "events.import.title": "📥 <b>Импорт событий</b>",
        "events.import.description": "Пожалуйста, загрузите файл в формате .ics в чат",
        "events.export.selected": "📥 Экспорт событий выбран",
        "events.export.title": "📥 <b>Экспорт событий</b>",
        "events.export.description": "Это ваши события в формате .ics (только внутренние события)",
        "events.create.selected": "➕ Создание события выбрано",
        "events.create.title": "➕ <b>Создание событий</b>",
        "events.view.selected": "🔍 Просмотр событий выбран",
        "events.view.title": "🔍 <b>Просмотр событий</b>",
        "events.feature_dev": "Функция находится в разработке.",
        # Create event
        "create_event.enter_title": "📝 Введите название события:\n\n",
        "create_event.cancelled": "❌ Создание события отменено",
        "create_event.title_empty": "❌ Название не должно быть пустым",
        "create_event.title_too_long": "❌ Название слишком длинное (максимум 100 символов)",
        "create_event.enter_description": "📄 Введите описание:\n\n",
        "create_event.enter_date": "📅 Введите дату начала:\n\nФормат: ДД.ММ.ГГГГ (пример: 25.12.2025)",
        "create_event.date_format_error": "❌ Неверный формат даты\n\nФормат: ДД.ММ.ГГГГ (пример: 25.12.2025)",
        "create_event.enter_time": "⏰ Введите время начала:\n\nФормат: ЧЧ:ММ (пример: 14:30)",
        "create_event.time_format_error": "❌ Неверный формат времени\n\nИспользуйте формат: ЧЧ:ММ (пример: 14:30)",
        "create_event.preview.title": "📋 Проверьте данные события:",
        "create_event.preview.title_label": "📝 <b>Название:</b> {title}",
        "create_event.preview.description_label": "📄 <b>описание:</b> {description}",
        "create_event.preview.date_label": "📅 <b>Дата начала:</b> {date}",
        "create_event.preview.time_label": "⏰ <b>Время начала:</b> {time}",
        "create_event.preview.confirm": "✅ Всё правильно?",
        "create_event.preview.description_none": "(Нет)",
        "create_event.confirmed": "✅ Событие создано!",
        "create_event.success": "✅ <b>Событие успешно создано</b>",
        # Calendar
        "calendar.link.title": "🔗 <b>Связать календарь</b>\n\nВыберите действие:",
        "calendar.list.answer": "📑 Ваши календари",
        "calendar.list.title": "📑 <b>Ваши календари</b>",
        "calendar.list.linked": "<b>Связанные календари:</b>",
        "calendar.list.feature_dev": "Функция находится в разработке. Здесь вы можете отвязать календари.",
        "calendar.new.answer": "🔗 Связать новый календарь",
        "calendar.new.title": "🔗 <b>Связать новый календарь</b>",
        "calendar.new.enter_link": "<b>Введите ссылку на ical:</b>",
        # Daily plan
        "daily_plan.generating": "📋 Генерация ежедневного плана...",
        "daily_plan.end": "Конец ежедневного плана",
        # Buttons - Main menu
        "btn.settings": "⚙️ Настройки",
        "btn.events": "📅 События",
        "btn.daily_plan": "📋 Получить ежедневный план",
        "btn.external_calendars": "🔗 Внешние календари",
        "btn.back": "« Назад",
        # Buttons - Settings
        "btn.timezone": "🌍 Часовой пояс",
        "btn.language": "🇬🇧 Язык",
        "btn.quiet_hours": "🔇 Тихие часы",
        "btn.daily_plans_time": "⏰ Время ежедневных планов",
        # Buttons - Events
        "btn.import": "📥 Импорт",
        "btn.export": "📤 Экспорт",
        "btn.add": "➕ Добавить",
        "btn.view": "🔍 Просмотр",
        "btn.create_by_dialog": "📅 Создать через диалог",
        # Buttons - Calendar
        "btn.calendar_list": "📑 Список календарей",
        "btn.link_calendar": "🔗 Связать новый календарь",
        # Buttons - Language
        "btn.language.en": "English",
        "btn.language.ru": "Русский",
        # Buttons - Quiet hours
        "btn.quiet_hours.enter": "ввести тихие часы",
        # Buttons - Daily plan time
        "btn.daily_plan_time.enter": "ввести время ежедневных планов",
        # Buttons - Actions
        "btn.cancel": "❌ Отмена",
        "btn.skip": "⏭ Пропустить",
        "btn.accept": "✅ Принять",
        "btn.reject": "❌ Отклонить",
        "btn.delete": "❌ удалить",
        "btn.edit": "✎ редактировать",
        # Calendar widget
        "calendar.prev_month": "<<",
        "calendar.next_month": ">>",
        "calendar.weekdays": "Пн,Вт,Ср,Чт,Пт,Сб,Вс",
    },
}


def t(key: str, lang: str = "ru", **kwargs: str) -> str:
    """Return translation string by key.

    Args:
        key: Translation key (e.g., "start.welcome").
        lang: Language code ("en" or "ru"). Defaults to "ru".
        **kwargs: Format arguments for string formatting.

    Returns:
        Translated string with format arguments applied. Falls back to English
        if key is missing in selected language.
    """
    strings = STRINGS.get(lang, STRINGS["en"])
    result = strings.get(key, STRINGS["en"].get(key, key))
    if kwargs:
        try:
            return result.format(**kwargs)
        except KeyError:
            return result
    return result
