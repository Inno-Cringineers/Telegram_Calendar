import asyncio
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.database import UnitOfWork
from logger.logger import logger
from store.store import Store


@dataclass
class CalendarQueueItem:
    calendar_id: int
    calendar_name: str
    calendar_url: str
    user_id: int


class SyncWorker:
    def __init__(
        self, queue: asyncio.Queue[CalendarQueueItem | None], session_maker: async_sessionmaker[AsyncSession]
    ) -> None:
        self.queue = queue
        self.session_maker = session_maker

    async def run(self) -> None:
        """Run the sync worker."""
        while True:
            # get calendar from queue
            calendar = await self.queue.get()

            # for graceful shutdown
            if calendar is None:
                self.queue.task_done()
                logger.debug("Sync worker: stopped by queue.get() return None")
                break

            logger.debug(
                "Sync worker: got calendar from queue",
                extra={
                    "calendar_id": calendar.calendar_id,
                    "calendar_name": calendar.calendar_name,
                    "calendar_url": calendar.calendar_url,
                },
            )

            # upload calendar to server
            try:
                # create store
                async with UnitOfWork(self.session_maker) as uow:
                    session = uow.session
                    if session is None:
                        raise RuntimeError("Session is None")
                    store = Store(session)
                    await store.UploadService.upload_ical_url(
                        calendar.user_id, calendar.calendar_name, calendar.calendar_url
                    )
                    logger.debug(
                        "Sync worker: uploaded calendar to server", extra={"calendar_id": calendar.calendar_id}
                    )
            except Exception as e:
                logger.error("Error syncing calendar", exc_info=e, extra={"calendar_id": calendar.calendar_id})
            finally:
                self.queue.task_done()


class SyncService:
    def __init__(
        self,
        session_maker: async_sessionmaker[AsyncSession],
        sync_interval: timedelta,
        sync_workers: int,
    ) -> None:
        self.session_maker = session_maker
        self.sync_interval = sync_interval
        self.sync_workers = sync_workers
        self.queue: asyncio.Queue[CalendarQueueItem | None] = asyncio.Queue[CalendarQueueItem | None]()
        self.workers: list[SyncWorker] = []
        self.worker_tasks: list[asyncio.Task] = []

    async def start_sync_service(self) -> None:
        """Start the sync service."""
        logger.info(
            "Starting sync service", extra={"sync_interval": self.sync_interval, "sync_workers": self.sync_workers}
        )

        # initialize workers
        for _ in range(self.sync_workers):
            worker = SyncWorker(self.queue, self.session_maker)
            task = asyncio.create_task(worker.run())
            self.worker_tasks.append(task)

        # start sync loop
        while True:
            await self.load_calendars_to_queue()
            await asyncio.sleep(self.sync_interval.total_seconds())

    async def load_calendars_to_queue(self) -> None:
        """Sync calendars."""
        logger.info("Syncing calendars")
        # get calendars from database

        async with UnitOfWork(self.session_maker) as uow:
            session = uow.session
            if session is None:
                raise RuntimeError("Session is None")
            store = Store(session)
            calendars = await store.CalendarService.get_externals_to_sync()

            if calendars == []:
                logger.debug("No calendars to load to queue")
                return
            for calendar in calendars:
                logger.debug(
                    "Loading calendar to queue",
                    extra={
                        "calendar_id": calendar.id,
                        "calendar_name": calendar.name,
                        "calendar_url": calendar.url,
                    },
                )
                await self.queue.put(CalendarQueueItem(calendar.id, calendar.name, calendar.url, calendar.user_id))  # type: ignore

        logger.info("Calendars loaded to queue")

    async def stop(self):
        """graceful shutdown"""
        logger.info("Stopping sync service")
        for _ in range(self.sync_workers):
            await self.queue.put(None)
        await asyncio.gather(*self.worker_tasks)
