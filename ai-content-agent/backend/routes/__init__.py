"""
API route modules.
"""

from routes.auth import router as auth_router
from routes.oauth import router as oauth_router
from routes.campaigns import router as campaigns_router
from routes.content import router as content_router, content_router as content_management_router
from routes.schedule import router as schedule_router
from routes.analytics import router as analytics_router

__all__ = ["auth_router", "oauth_router", "campaigns_router", "content_router", "content_management_router", "schedule_router", "analytics_router"]
