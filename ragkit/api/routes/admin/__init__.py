"""Admin API routes."""

from fastapi import APIRouter

from ragkit.api.routes.admin.config import router as config_router
from ragkit.api.routes.admin.health import router as health_router
from ragkit.api.routes.admin.ingestion import router as ingestion_router
from ragkit.api.routes.admin.metrics import router as metrics_router

admin_router = APIRouter(prefix="/admin", tags=["admin"])
admin_router.include_router(config_router)
admin_router.include_router(ingestion_router)
admin_router.include_router(metrics_router)
admin_router.include_router(health_router)

__all__ = ["admin_router"]
