"""
Base repository class providing common functionality for all repositories.

This abstract base class can be easily mocked in tests and ensures
consistent interface across all repositories.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")  # Entity type


class BaseRepository(ABC, Generic[T]):
    """Abstract base class for all repositories.

    Provides common interface and can be easily mocked in tests.
    All repositories should inherit from this class.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with a database session.

        Args:
            session: SQLAlchemy async session to use for database operations.
        """
        self.session = session

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> T | None:
        """Retrieve an entity by its ID.

        Args:
            entity_id: The ID of the entity to retrieve.

        Returns:
            The entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def create(self, **kwargs) -> T:
        """Create a new entity.

        Args:
            **kwargs: Entity attributes.

        Returns:
            The created entity.
        """
        pass

    @abstractmethod
    async def update(self, entity_id: int, **kwargs) -> T:
        """Update an existing entity.

        Args:
            entity_id: The ID of the entity to update.
            **kwargs: Attributes to update.

        Returns:
            The updated entity.

        Raises:
            NotFoundError: If the entity is not found.
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: int) -> None:
        """Delete an entity by ID.

        Args:
            entity_id: The ID of the entity to delete.

        Raises:
            NotFoundError: If the entity is not found.
        """
        pass

