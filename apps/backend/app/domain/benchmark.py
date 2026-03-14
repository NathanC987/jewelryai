from pydantic import BaseModel


class OperationLatencyMetrics(BaseModel):
    operation: str
    samples: int
    min_ms: float
    avg_ms: float
    max_ms: float


class EditLatencyBenchmarkResponse(BaseModel):
    ring_id: str
    iterations: int
    target_max_ms: float
    meets_target: bool
    overall_max_ms: float
    per_operation: list[OperationLatencyMetrics]
