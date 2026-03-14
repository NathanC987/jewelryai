from fastapi import APIRouter, HTTPException

from app.domain.export import ExportResponse
from app.services.export_service import export_service

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/{ring_id}/glb", response_model=ExportResponse)
def export_glb(ring_id: str) -> ExportResponse:
    result = export_service.get_export(ring_id, "glb")
    if not result:
        raise HTTPException(status_code=404, detail="Ring not found")
    return result


@router.get("/{ring_id}/stl", response_model=ExportResponse)
def export_stl(ring_id: str) -> ExportResponse:
    result = export_service.get_export(ring_id, "stl")
    if not result:
        raise HTTPException(status_code=404, detail="Ring not found")
    return result
