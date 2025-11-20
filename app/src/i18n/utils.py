"""Utility functions for i18n."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.settings import Settings


async def get_user_language(session: AsyncSession, user_id: int) -> str:
    """Get user language from settings.

    Args:
        session: Database session.
        user_id: Telegram user ID.

    Returns:
        Language code ("en" or "ru"). Defaults to "ru" if not found.
    """
    result = await session.execute(select(Settings).where(Settings.user_id == user_id))
    settings = result.scalar_one_or_none()
    if settings and settings.language:
        return settings.language
    return "ru"

