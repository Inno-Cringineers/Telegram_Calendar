"""
This module defines the `FSMState` class, which represents FSM state storage in PostgreSQL.
"""

from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class FSMState(Base):
    """Represents FSM state storage in PostgreSQL.

    Stores aiogram FSM state and data for each user/chat combination.
    The key format is: "fsm:{bot_id}:{chat_id}:{user_id}"

    Attributes:
        key: str - Primary key, format: "fsm:{bot_id}:{chat_id}:{user_id}".
        state: str | None - Current FSM state name (None if no state is set).
        data: dict[str, Any] - FSM state data as JSON dictionary.
    """

    key: Mapped[str] = mapped_column(String, primary_key=True)
    state: Mapped[str | None] = mapped_column(String, nullable=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

