"""Whitelist middleware for user access restriction.

This middleware checks if a user's username is in the whitelist before allowing
access to the bot. The whitelist is loaded from a JSON file and automatically
reloaded when the file changes (hot reload).
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from logger.logger import logger


class WhitelistMiddleware(BaseMiddleware):
    """Middleware that restricts bot access to whitelisted users only.

    Checks if the user's username is in the whitelist file. If user restriction
    is disabled, all users are allowed. The whitelist file is automatically
    reloaded when it changes.

    Attributes:
        whitelist_path: Path to the whitelist JSON file.
        enabled: Whether user restriction is enabled.
        _whitelist: Current set of whitelisted usernames.
        _last_modified: Last modification time of the whitelist file.
        _reload_task: Background task for monitoring file changes.
    """

    def __init__(self, whitelist_path: str | Path, enabled: bool = True) -> None:
        """Initialize whitelist middleware.

        Args:
            whitelist_path: Path to the whitelist JSON file.
            enabled: Whether user restriction is enabled. If False, all users are allowed.
        """
        super().__init__()
        self.whitelist_path = Path(whitelist_path)
        self.enabled = enabled
        self._whitelist: set[str] = set()
        self._last_modified: float = 0.0
        self._reload_task: asyncio.Task[None] | None = None

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Check if user is whitelisted before calling handler.

        Args:
            handler: The next handler to call.
            event: Incoming update/event object (Message or CallbackQuery).
            data: Aiogram data dict.

        Returns:
            Whatever the handler returns, or None if user is not whitelisted.
        """
        # If restriction is disabled, allow all users
        if not self.enabled:
            return await handler(event, data)

        # Extract username from event
        username: str | None = None
        if isinstance(event, Message) and event.from_user:
            username = event.from_user.username
        elif isinstance(event, CallbackQuery) and event.from_user:
            username = event.from_user.username

        # If user has no username, deny access
        if not username:
            logger.warning(
                f"WhitelistMiddleware: User {event.from_user.id if hasattr(event, 'from_user') and event.from_user else 'unknown'} "
                "has no username, access denied"
            )
            await self._send_access_denied_message(event)
            return None

        # Check if username is in whitelist (with @ prefix)
        username_with_at = f"@{username}" if not username.startswith("@") else username

        if username_with_at not in self._whitelist:
            logger.warning(
                f"WhitelistMiddleware: User @{username} (ID: {event.from_user.id if hasattr(event, 'from_user') and event.from_user else 'unknown'}) "
                "is not in whitelist, access denied"
            )
            await self._send_access_denied_message(event)
            return None

        logger.debug(f"WhitelistMiddleware: User @{username} is whitelisted, allowing access")
        return await handler(event, data)

    async def _send_access_denied_message(self, event: TelegramObject) -> None:
        """Send access denied message to user.

        Args:
            event: Telegram event (Message or CallbackQuery).
        """
        message_text = "❌ You don't have access to this bot."

        try:
            if isinstance(event, Message):
                await event.answer(message_text)
            elif isinstance(event, CallbackQuery):
                await event.answer(message_text, show_alert=True)
        except Exception as e:
            logger.error(f"WhitelistMiddleware: Failed to send access denied message: {str(e)}", exc_info=True)

    def load_whitelist(self) -> None:
        """Load whitelist from JSON file.

        Reads the whitelist file and updates the internal whitelist set.
        If the file doesn't exist or is invalid, logs an error and uses an empty set.
        """
        try:
            if not self.whitelist_path.exists():
                logger.warning(f"WhitelistMiddleware: Whitelist file not found: {self.whitelist_path}")
                self._whitelist = set()
                return

            with open(self.whitelist_path, encoding="utf-8") as f:
                data = json.load(f)

            # Support both list and dict formats
            if isinstance(data, list):
                usernames = [str(u).strip() for u in data if u]
            elif isinstance(data, dict) and "usernames" in data:
                usernames = [str(u).strip() for u in data["usernames"] if u]
            else:
                logger.error(f"WhitelistMiddleware: Invalid whitelist format in {self.whitelist_path}")
                self._whitelist = set()
                return

            # Normalize usernames (ensure they start with @)
            normalized_usernames = set()
            for username in usernames:
                if username:
                    if not username.startswith("@"):
                        username = f"@{username}"
                    normalized_usernames.add(username)

            self._whitelist = normalized_usernames
            logger.info(f"WhitelistMiddleware: Loaded {len(self._whitelist)} usernames from {self.whitelist_path}")

        except json.JSONDecodeError as e:
            logger.error(f"WhitelistMiddleware: Invalid JSON in whitelist file: {str(e)}", exc_info=True)
            self._whitelist = set()
        except Exception as e:
            logger.error(f"WhitelistMiddleware: Failed to load whitelist: {str(e)}", exc_info=True)
            self._whitelist = set()

    async def start_file_watcher(self) -> None:
        """Start background task to monitor whitelist file for changes.

        Checks the file modification time every 2 seconds and reloads
        the whitelist if the file has been modified.
        """
        # Load initial whitelist
        self.load_whitelist()
        self._last_modified = self.whitelist_path.stat().st_mtime if self.whitelist_path.exists() else 0.0

        async def watch_file() -> None:
            """Monitor file for changes."""
            while True:
                try:
                    await asyncio.sleep(2)  # Check every 2 seconds

                    if not self.whitelist_path.exists():
                        continue

                    current_modified = self.whitelist_path.stat().st_mtime
                    if current_modified > self._last_modified:
                        logger.info("WhitelistMiddleware: Whitelist file changed, reloading...")
                        self._last_modified = current_modified
                        self.load_whitelist()

                except asyncio.CancelledError:
                    logger.debug("WhitelistMiddleware: File watcher cancelled")
                    break
                except Exception as e:
                    logger.error(f"WhitelistMiddleware: Error in file watcher: {str(e)}", exc_info=True)
                    await asyncio.sleep(5)  # Wait longer on error

        self._reload_task = asyncio.create_task(watch_file())
        logger.info("WhitelistMiddleware: File watcher started")

    async def stop_file_watcher(self) -> None:
        """Stop the file watcher task."""
        if self._reload_task and not self._reload_task.done():
            self._reload_task.cancel()
            try:
                await self._reload_task
            except asyncio.CancelledError:
                pass
            logger.info("WhitelistMiddleware: File watcher stopped")
