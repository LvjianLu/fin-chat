from fastapi import APIRouter

router = APIRouter()

# Import and include routers
from finchat_backend.api.v1 import chat, sessions, files

router.include_router(chat.router)
router.include_router(sessions.router)
router.include_router(files.router)

__all__ = ["router"]
