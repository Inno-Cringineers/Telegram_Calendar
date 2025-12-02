# Localization with Babel

This project uses Babel for internationalization (i18n) support.

## Structure

- `strings.py` - Main translation function `t()` that uses Babel's gettext
- `locales/` - Directory containing translation files
  - `en/LC_MESSAGES/` - English translations
  - `ru/LC_MESSAGES/` - Russian translations
    - `messages.po` - Portable Object file (human-readable translations)
    - `messages.mo` - Machine Object file (compiled binary format)

## Usage

### In Handlers

Language is automatically injected by `SettingsMiddleware` into the `data` dict:

```python
async def my_handler(message: Message, data: dict) -> None:
    lang = data.get("lang", "en")
    text = t("start.welcome", lang=lang, user_name=user_name)
```

### In Keyboards

Keyboards receive `lang` as a parameter:

```python
def get_main_menu_inline(lang: str = "en") -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=t("btn.settings", lang=lang), ...)],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
```

## Compiling Translations

After installing Babel (`pip install Babel`), compile .po files to .mo files:

```bash
python scripts/compile_messages.py
```

Or manually using Babel:

```bash
pybabel compile -d src/i18n/locales
```

## Adding New Translations

1. Edit the `.po` files in `locales/{lang}/LC_MESSAGES/messages.po`
2. Compile to `.mo` files using the script above
3. Restart the application

## Translation Keys

Translation keys use dot notation (e.g., `start.welcome`), which are converted to underscores (`start_welcome`) for Babel's gettext system.

