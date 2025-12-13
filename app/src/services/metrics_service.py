"""
Metrics service for collecting database metrics and exporting them to Grafana via OpenTelemetry.

This service periodically collects metrics from the database:
- User language distribution
- Events count with URL (from external calendars)
- Events count without URL (manually created)
"""

import asyncio
from collections.abc import Iterable
from datetime import timedelta

from opentelemetry import metrics
from opentelemetry.metrics import CallbackOptions, Observation
from sqlalchemy import func, join, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.database import UnitOfWork
from logger.logger import logger
from models.calendar import Calendar
from models.event import Event
from models.settings import Settings


class MetricsService:
    """Service for collecting and exporting database metrics to Grafana."""

    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        update_interval: timedelta,
    ) -> None:
        """Initialize MetricsService.

        Args:
            session_maker: Async session maker for database access.
            update_interval: Interval between metric updates.
        """
        self.session_maker = session_maker
        self.update_interval = update_interval
        self._running = False

        # Store current metric values for ObservableGauge callbacks
        self._language_counts: dict[str, int] = {}
        self._events_with_url: int = 0
        self._events_without_url: int = 0

        # Get meter from OpenTelemetry
        meter = metrics.get_meter(__name__)

        # Create observable gauges with callbacks
        # User language distribution gauge (with language label)
        self.user_language_gauge = meter.create_observable_gauge(
            name="user_language_count",
            description="Number of users by language",
            unit="1",
            callbacks=[self._observe_user_languages],
        )

        # Events with URL gauge
        self.events_with_url_gauge = meter.create_observable_gauge(
            name="events_with_url_count",
            description="Total number of events from external calendars (with URL)",
            unit="1",
            callbacks=[self._observe_events_with_url],
        )

        # Events without URL gauge
        self.events_without_url_gauge = meter.create_observable_gauge(
            name="events_without_url_count",
            description="Total number of manually created events (without URL)",
            unit="1",
            callbacks=[self._observe_events_without_url],
        )

    async def start_metrics_service(self) -> None:
        """Start the metrics collection service."""
        logger.info(
            "Starting metrics service",
            extra={"update_interval": self.update_interval},
        )
        self._running = True

        # Initial collection
        await self.collect_metrics()

        # Periodic collection
        while self._running:
            await asyncio.sleep(self.update_interval.total_seconds())
            if self._running:
                await self.collect_metrics()

    async def collect_metrics(self) -> None:
        """Collect metrics from database and update OpenTelemetry metrics."""
        try:
            logger.debug("Collecting metrics from database")

            async with UnitOfWork(self.session_maker) as uow:
                session = uow.session
                if session is None:
                    raise RuntimeError("Session is None")

                # Collect user language distribution
                await self._collect_user_languages(session)

                # Collect events counts
                await self._collect_events_counts(session)

            logger.debug("Metrics collected successfully")
        except Exception as e:
            logger.error("Error collecting metrics", exc_info=e)

    def _observe_user_languages(self, options: CallbackOptions) -> Iterable[Observation]:
        """Callback for observing user language distribution.

        Args:
            options: Callback options.

        Returns:
            Iterable of observations for each language.
        """
        return [Observation(count, {"language": language}) for language, count in self._language_counts.items()]

    async def _collect_user_languages(self, session: AsyncSession) -> None:
        """Collect user language distribution from settings table.

        Args:
            session: Database session.
        """
        # Query: SELECT language, COUNT(*) FROM settings GROUP BY language
        stmt = select(Settings.language, func.count(Settings.id).label("count")).group_by(Settings.language)
        result = await session.execute(stmt)
        rows = result.all()

        # Update stored values for ObservableGauge callback
        self._language_counts = {}
        for language, count in rows:
            self._language_counts[language] = count

        logger.debug(
            "Collected user language metrics",
            extra={"language_counts": self._language_counts},
        )

    def _observe_events_with_url(self, options: CallbackOptions) -> Iterable[Observation]:
        """Callback for observing events with URL count.

        Args:
            options: Callback options.

        Returns:
            Single observation with events with URL count.
        """
        return [Observation(self._events_with_url)]

    def _observe_events_without_url(self, options: CallbackOptions) -> Iterable[Observation]:
        """Callback for observing events without URL count.

        Args:
            options: Callback options.

        Returns:
            Single observation with events without URL count.
        """
        return [Observation(self._events_without_url)]

    async def _collect_events_counts(self, session: AsyncSession) -> None:
        """Collect events counts (with/without URL) from database.

        Args:
            session: Database session.
        """
        # Query for events with URL (from external calendars)
        # SELECT COUNT(*) FROM event e JOIN calendar c ON e.calendar_id = c.id WHERE c.url IS NOT NULL
        stmt_with_url = (
            select(func.count(Event.id))
            .select_from(join(Event, Calendar, Event.calendar_id == Calendar.id))
            .where(Calendar.url.isnot(None))
        )
        result_with_url = await session.execute(stmt_with_url)
        self._events_with_url = result_with_url.scalar() or 0

        # Query for events without URL (manually created)
        # SELECT COUNT(*) FROM event e JOIN calendar c ON e.calendar_id = c.id WHERE c.url IS NULL
        stmt_without_url = (
            select(func.count(Event.id))
            .select_from(join(Event, Calendar, Event.calendar_id == Calendar.id))
            .where(Calendar.url.is_(None))
        )
        result_without_url = await session.execute(stmt_without_url)
        self._events_without_url = result_without_url.scalar() or 0

        logger.debug(
            "Collected events metrics",
            extra={
                "events_with_url": self._events_with_url,
                "events_without_url": self._events_without_url,
            },
        )

    async def stop(self) -> None:
        """Stop the metrics service gracefully."""
        logger.info("Stopping metrics service")
        self._running = False
