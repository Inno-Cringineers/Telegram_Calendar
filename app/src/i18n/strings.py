"""Localization strings for user-facing text using Babel.

All user-facing strings are managed through Babel's gettext system.
"""

from gettext import translation
from pathlib import Path
from typing import Any

# Path to locales directory
LOCALES_DIR = Path(__file__).parent / "locales"

# Supported languages
SUPPORTED_LANGUAGES = ["en", "ru"]
DEFAULT_LANGUAGE = "en"


def get_translator(lang: str = DEFAULT_LANGUAGE) -> Any:
    """Get translation object for specified language.

    Args:
        lang: Language code ("en" or "ru"). Defaults to "en".

    Returns:
        Translation object for the specified language.
    """
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    try:
        return translation("messages", localedir=str(LOCALES_DIR), languages=[lang], fallback=True)  # type: ignore[return-value]
    except Exception:
        # Fallback to default language if translation fails
        return translation("messages", localedir=str(LOCALES_DIR), languages=[DEFAULT_LANGUAGE], fallback=True)  # type: ignore[return-value]


def t(key: str, lang: str = DEFAULT_LANGUAGE, **kwargs: str) -> str:
    """Return translation string by key using Babel.

    Args:
        key: Translation key (e.g., "start.welcome").
        lang: Language code ("en" or "ru"). Defaults to "en".
        **kwargs: Format arguments for string formatting.

    Returns:
        Translated string with format arguments applied. Falls back to key
        if translation is missing.
    """
    translator = get_translator(lang)
    # Convert key format (dots to underscores) to match .po file format
    message_id = key.replace(".", "_")
    result = translator.gettext(message_id)

    # If translation not found (returns the same string), try English
    if result == message_id and lang != DEFAULT_LANGUAGE:
        default_translator = get_translator(DEFAULT_LANGUAGE)
        result = default_translator.gettext(message_id)

    # If still not found, return the original key
    if result == message_id:
        result = key

    # Apply format arguments if provided
    if kwargs:
        try:
            return result.format(**kwargs)
        except (KeyError, ValueError):
            return result

    return result
