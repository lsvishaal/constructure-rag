"""API routers module."""
from src.api.auth import router as auth_router
from src.api.chat import router as chat_router
from src.api.documents import router as documents_router
from src.api.health import router as health_router

__all__ = ["auth_router", "chat_router", "documents_router", "health_router"]
