"""PostgreSQL storage for aiogram FSM."""

from collections.abc import Mapping
from typing import Any

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from logger.logger import logger
from models.fsm_state import FSMState


class PostgresStorage(BaseStorage):
    """PostgreSQL-based storage for aiogram FSM.

    Stores FSM state and data in PostgreSQL database.
    This allows state to persist across bot restarts and enables
    horizontal scaling with multiple bot instances.

    Usage:
        session_maker = create_session_maker(engine)
        storage = PostgresStorage(session_maker)
        dp = Dispatcher(storage=storage)
    """

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        """Initialize PostgreSQL storage.

        Args:
            session_maker: Async session maker for database access.
        """
        self.session_maker = session_maker

    def _make_key(self, key: StorageKey) -> str:
        """Convert StorageKey to string format.

        Args:
            key: Storage key from aiogram.

        Returns:
            String representation of the key in format: "fsm:{bot_id}:{chat_id}:{user_id}".
        """
        return f"fsm:{key.bot_id}:{key.chat_id}:{key.user_id}"

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        """Set state for a key.

        Args:
            key: Storage key.
            state: State to set (None to clear state).
        """
        state_str = state.state if isinstance(state, State) else state
        db_key = self._make_key(key)

        async with self.session_maker() as session:
            async with session.begin():
                stmt = select(FSMState).where(FSMState.key == db_key)
                result = await session.execute(stmt)
                fsm_state = result.scalar_one_or_none()

                if fsm_state:
                    fsm_state.state = state_str
                else:
                    fsm_state = FSMState(key=db_key, state=state_str, data={})
                    session.add(fsm_state)

                logger.debug("FSM state set: key=%s, state=%s", db_key, state_str)

    async def get_state(self, key: StorageKey) -> str | None:
        """Get state for a key.

        Args:
            key: Storage key.

        Returns:
            State string or None if not found.
        """
        db_key = self._make_key(key)

        async with self.session_maker() as session:
            stmt = select(FSMState).where(FSMState.key == db_key)
            result = await session.execute(stmt)
            fsm_state = result.scalar_one_or_none()

            state_str = fsm_state.state if fsm_state else None
            logger.debug("FSM state retrieved: key=%s, state=%s", db_key, state_str)
            return state_str

    async def set_data(self, key: StorageKey, data: Mapping[str, Any]) -> None:
        """Set data for a key.

        Args:
            key: Storage key.
            data: Data mapping to store.
        """
        db_key = self._make_key(key)
        # Convert Mapping to dict for storage
        data_dict = dict(data)

        async with self.session_maker() as session:
            async with session.begin():
                stmt = select(FSMState).where(FSMState.key == db_key)
                result = await session.execute(stmt)
                fsm_state = result.scalar_one_or_none()

                if fsm_state:
                    fsm_state.data = data_dict
                else:
                    fsm_state = FSMState(key=db_key, state=None, data=data_dict)
                    session.add(fsm_state)

                logger.debug("FSM data set: key=%s, data_keys=%s", db_key, list(data_dict.keys()))

    async def get_data(self, key: StorageKey) -> dict[str, Any]:
        """Get data for a key.

        Args:
            key: Storage key.

        Returns:
            Data dictionary or empty dict if not found.
        """
        db_key = self._make_key(key)

        async with self.session_maker() as session:
            stmt = select(FSMState).where(FSMState.key == db_key)
            result = await session.execute(stmt)
            fsm_state = result.scalar_one_or_none()

            data = fsm_state.data if fsm_state else {}
            logger.debug("FSM data retrieved: key=%s, data_keys=%s", db_key, list(data.keys()) if data else [])
            return data

    async def update_data(self, key: StorageKey, data: Mapping[str, Any]) -> dict[str, Any]:
        """Update data for a key (merge with existing).

        Args:
            key: Storage key.
            data: Data mapping to merge with existing data.

        Returns:
            Updated data dictionary.
        """
        current_data = await self.get_data(key)
        current_data.update(data)
        await self.set_data(key, current_data)
        return current_data

    async def close(self) -> None:
        """Close storage (no-op for PostgreSQL).

        PostgreSQL connections are managed by session_maker,
        so no explicit cleanup is needed here.
        """
        logger.debug("PostgresStorage.close() called (no-op)")

    async def clear(self, key: StorageKey) -> None:
        """Clear state and data for a key.

        Args:
            key: Storage key to clear.
        """
        db_key = self._make_key(key)

        async with self.session_maker() as session:
            async with session.begin():
                stmt = delete(FSMState).where(FSMState.key == db_key)
                await session.execute(stmt)
                logger.debug("FSM state cleared: key=%s", db_key)
