from fastapi import APIRouter, HTTPException, Query

from app.domain.ring import (
    PromptRingGenerateRequest,
    PromptRingGenerateResponse,
    RingGraphResponse,
    RingParameters,
    RingStateResponse,
    RingVariationSetResponse,
    RingUpdateRequest,
)
from app.services.prompt_interpreter import prompt_interpreter_service
from app.services.ring_service import ring_service

router = APIRouter(prefix="/rings", tags=["rings"])


@router.post("/from-prompt", response_model=PromptRingGenerateResponse)
def create_ring_from_prompt(payload: PromptRingGenerateRequest) -> PromptRingGenerateResponse:
    interpretation, parameters = prompt_interpreter_service.interpret(payload.prompt)
    ring = ring_service.create_ring(parameters=parameters)
    return PromptRingGenerateResponse(interpretation=interpretation, ring=ring)


@router.post("", response_model=RingStateResponse)
def create_ring(parameters: RingParameters | None = None) -> RingStateResponse:
    return ring_service.create_ring(parameters=parameters)


@router.get("/{ring_id}", response_model=RingStateResponse)
def get_ring(ring_id: str) -> RingStateResponse:
    state = ring_service.get_ring(ring_id)
    if not state:
        raise HTTPException(status_code=404, detail="Ring not found")
    return state


@router.get("/{ring_id}/graph", response_model=RingGraphResponse)
def get_ring_graph(ring_id: str) -> RingGraphResponse:
    graph = ring_service.get_graph(ring_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Ring not found")
    return graph


@router.patch("/{ring_id}", response_model=RingStateResponse)
def patch_ring(ring_id: str, update: RingUpdateRequest) -> RingStateResponse:
    state = ring_service.update_ring(ring_id, update)
    if not state:
        raise HTTPException(status_code=404, detail="Ring not found")
    return state


@router.post("/{ring_id}/variations", response_model=RingVariationSetResponse)
def generate_ring_variations(
    ring_id: str,
    count: int = Query(default=5, ge=1, le=5),
) -> RingVariationSetResponse:
    variations = ring_service.generate_variations(ring_id, count=count)
    if not variations:
        raise HTTPException(status_code=404, detail="Ring not found")
    return variations
