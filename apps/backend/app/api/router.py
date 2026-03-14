from fastapi import APIRouter

from app.api.routes.benchmarks import router as benchmarks_router
from app.api.routes.exports import router as exports_router
from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.rings import router as rings_router
from app.api.routes.sketches import router as sketches_router

api_router = APIRouter()
api_router.include_router(benchmarks_router)
api_router.include_router(exports_router)
api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(rings_router)
api_router.include_router(sketches_router)
