from fastapi import APIRouter, HTTPException

from app.domain.ring import (
    RingChangePromptRequest,
    PromptRingGenerateRequest,
    PromptRingGenerateResponse,
    RingGraphResponse,
    RingParameters,
    RingStateResponse,
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


@router.post("/{ring_id}/change-prompt", response_model=RingStateResponse)
def apply_change_prompt(ring_id: str, payload: RingChangePromptRequest) -> RingStateResponse:
    current = ring_service.get_ring(ring_id)
    if not current:
        raise HTTPException(status_code=404, detail="Ring not found")

    update = prompt_interpreter_service.interpret_change_prompt(payload.prompt, current.parameters)
    state = ring_service.update_ring(ring_id, update)
    if not state:
        raise HTTPException(status_code=404, detail="Ring not found")
    return state


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


