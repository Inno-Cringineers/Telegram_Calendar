Your task is to refactor the entire project according to the following mandatory rules. Apply all rules globally and consistently across all files. After each step, run `mypy` automatically and fix all typing issues before proceeding.
Never break existing tests. Never remove functionality.
If something is unclear — choose the safest option.

---

## ✅ 1. Run mypy and fully fix typing issues

- Run mypy on the entire project.
- For every error or warning:

  - Fix the underlying code, not by adding # type: ignore, unless absolutely unavoidable.
  - Use correct SQLAlchemy 2.0 typing (Mapped, mapped_column, AsyncSession, async_sessionmaker, etc.).
  - Fix @declared_attr warnings by replacing:

        @declared_attr

    def **tablename**(cls) -> str:
    return cls.**name**.lower()

    with SQLAlchemy-correct version:

        @declared_attr.directive

    def **tablename**(cls) -> str:
    return cls.**name**.lower()

  - Make sure middleware, async contexts, dependency injections, etc., are properly typed.

---

## ✅ 2. Extract ALL user-facing text into localization dictionaries

- Find all strings shown to the end user in:

  - buttons
  - messages
  - notifications
  - prompts
  - errors
  - titles / subtitles
  - reminders
  - logs intended for user visibility
  - inline keyboards
  - reply keyboards

- Move them into a new module:

src/bot/i18n/strings.py

### Structure:

STRINGS = {
"en": {
"start.welcome": "Welcome!",
"btn.ok": "OK",
"msg.error": "An error occurred.",
...
},
"ru": {
"start.welcome": "Добро пожаловать!",
"btn.ok": "ОК",
"msg.error": "Произошла ошибка.",
...
},
}

### Requirements:

- All text in the codebase MUST be accessed only via helper function:

from src.bot.i18n.strings import t
t("start.welcome", lang="ru")

- Implement the helper function:

def t(key: str, lang: str = "ru") -> str:
"""Return translation string by key."""

- Automatic fallback: if key is missing in selected language, fallback to English.

---

## ✅ 3. Apply Google-style docstrings to every file, class, and function

For example:

def get_engine(url: str) -> AsyncEngine:
"""Create an async SQLAlchemy engine.

    Args:
        url (str): Database connection URL.

    Returns:
        AsyncEngine: Configured SQLAlchemy async engine.
    """

### Rules:

- Every Python file must start with a short module-level docstring explaining the purpose of the file.
- Every class must have a class-level docstring.
- Every method and function must have:

  - short description
  - Args
  - Returns
  - Raises (if any)

---

## ✅ 4. Identify and extract duplicated logic

Search for duplicated code in:

- database setup
- session creation
- inline keyboard creation
- parsing dates
- logging calls
- reminders scheduling
- event time formatting
- checks like "if dates invalid → raise"
- access to user settings
- Base middleware patterns
- UnitOfWork / session management patterns

Whenever duplication is detected:

- Move repeated code into a shared utility module, for example:

src/bot/utils/dates.py
src/bot/utils/db.py
src/bot/utils/keyboards.py
src/bot/utils/validators.py

- Replace all occurrences with calls to the new helpers.

---

## ✅ 5. Modernize the code according to best practices for Aiogram 3.x

Ensure the following patterns are used:

### Middleware

- Use BaseMiddleware correctly (signature: **call**(handler, event, data)).
- Do not block event propagation.
- Ensure session injection uses async with.

### Dispatcher & Routers

- All handlers must be registered inside routers, not inside the main main.py.
- Use structured routers: e.g., calendar_router, settings_router.

### Keyboards

- Use factory functions for keyboards.
- No inline keyboards defined inline inside handlers.

### Async SQLAlchemy

- Use async_sessionmaker.
- Avoid session.commit() inside functions — use UnitOfWork.
- Improve UnitOfWork with proper typing & context boundaries.

### Logging

- Use structured logging (logger.bind(...)) where appropriate.
- Remove repeated log messages.

### Config

- Use Pydantic or at least a structured config module.

### Clean Architecture principles:

- No business logic inside handlers.
- No DB calls directly in router files — use service layer.

---

## ❗️ Mandatory constraints

- All changes must preserve current application behavior.
- All tests must pass without modification.
- New code must be typed, clean, and documented.
- If a change requires modifying tests, ask for confirmation before modifying test files.

---
