from aiogram import Router

from .handlers.start import router as start_router
from .handlers.create_event import router as create_event_router
from .handlers.menu import router as menu_router
from .handlers.settings import router as settings_router
from .handlers.events import router as events_router
from .handlers.calendar import router as calendar_router
from .handlers.daily_plan import router as daily_plan_router

router = Router()
router.include_router(start_router)
router.include_router(menu_router)
router.include_router(settings_router)
router.include_router(events_router)
router.include_router(calendar_router)
router.include_router(create_event_router)
router.include_router(daily_plan_router)


