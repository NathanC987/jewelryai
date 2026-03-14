from fastapi import APIRouter, Query

from app.core.config import settings
from app.domain.benchmark import EditLatencyBenchmarkResponse
from app.services.ring_service import ring_service

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.get("/edits", response_model=EditLatencyBenchmarkResponse)
def benchmark_edits(
    iterations: int = Query(default=settings.latency_benchmark_iterations, ge=1, le=500),
) -> EditLatencyBenchmarkResponse:
    return ring_service.benchmark_required_edits(
        iterations=iterations,
        target_max_ms=settings.latency_target_max_ms,
    )
