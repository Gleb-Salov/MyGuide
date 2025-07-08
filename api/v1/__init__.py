from .users_router import router as users_router
from .auth_router import router as auth_router
from .events_router import router as events_router



__all__ = [
    "users_router",
    "auth_router",
    "events_router"
]