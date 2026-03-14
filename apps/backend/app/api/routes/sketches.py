from fastapi import APIRouter, File, HTTPException, UploadFile

from app.domain.sketch import SketchAnalysisResponse, SketchUploadResponse
from app.services.sketch_service import sketch_service

router = APIRouter(prefix="/sketches", tags=["sketches"])


@router.post("/upload", response_model=SketchUploadResponse)
async def upload_sketch(file: UploadFile = File(...)) -> SketchUploadResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")

    try:
        return await sketch_service.ingest_sketch(file)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err


@router.get("/{sketch_id}/analysis", response_model=SketchAnalysisResponse)
def get_sketch_analysis(sketch_id: str) -> SketchAnalysisResponse:
    analysis = sketch_service.get_analysis(sketch_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Sketch analysis not found")
    return analysis
