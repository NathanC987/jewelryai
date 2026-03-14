from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.domain.sketch import (
    SketchAnalysisResponse,
    SketchUploadResponse,
)
from app.core.config import settings
from app.services.sketch_analysis import create_sketch_analyzer
from app.services.sketch_analysis.base import SketchAnalyzer


ARTIFACTS_ROOT = Path(__file__).resolve().parents[2] / "artifacts"
SKETCH_ARTIFACTS = ARTIFACTS_ROOT / "sketches"


class SketchService:
    def __init__(
        self,
        analyzer: SketchAnalyzer | None = None,
        analysis_backend: str | None = None,
    ) -> None:
        requested_backend = analysis_backend or settings.sketch_analysis_backend
        if analyzer is not None:
            self._analysis_backend = requested_backend
            self._analyzer = analyzer
        else:
            resolved_analyzer, resolved_backend = create_sketch_analyzer(
                requested_backend,
                fallback_backend=settings.sketch_analysis_fallback_backend,
                allow_fallback=settings.sketch_analysis_allow_fallback,
                device=settings.sketch_analysis_device,
                grounded_sam_mode=settings.sketch_analysis_grounded_sam_mode,
                grounding_dino_model_id=settings.grounding_dino_model_id,
                sam2_model_id=settings.sam2_model_id,
                        grounding_dino_checkpoint_path=settings.grounding_dino_checkpoint_path,
                        sam2_checkpoint_path=settings.sam2_checkpoint_path,
                        grounding_dino_box_threshold=settings.grounding_dino_box_threshold,
                        grounding_dino_text_threshold=settings.grounding_dino_text_threshold,
                        grounding_dino_local_files_only=settings.grounding_dino_local_files_only,
            )
            self._analysis_backend = resolved_backend
            self._analyzer = resolved_analyzer
        self._analysis_store: dict[str, SketchAnalysisResponse] = {}

    async def ingest_sketch(self, file: UploadFile) -> SketchUploadResponse:
        content = await file.read()
        if not content:
            raise ValueError("Uploaded sketch is empty")

        sketch_id = str(uuid4())
        extension = _infer_extension(file.filename)
        sketch_path = SKETCH_ARTIFACTS / f"{sketch_id}{extension}"
        sketch_path.parent.mkdir(parents=True, exist_ok=True)
        sketch_path.write_bytes(content)

        artifact_uri = f"/artifacts/sketches/{sketch_id}{extension}"
        draft = self._analyzer.analyze(content)
        analysis = SketchAnalysisResponse(
            sketch_id=sketch_id,
            artifact_uri=artifact_uri,
            analysis_backend=self._analysis_backend,
            components=draft.components,
            extracted_parameters=draft.extracted_parameters,
            feature_confidences=draft.feature_confidences,
            requires_user_confirmation=draft.requires_user_confirmation,
        )
        self._analysis_store[sketch_id] = analysis

        return SketchUploadResponse(
            sketch_id=sketch_id,
            artifact_uri=artifact_uri,
            analysis_uri=f"/api/v1/sketches/{sketch_id}/analysis",
            analysis_backend=self._analysis_backend,
            extracted_parameters=draft.extracted_parameters,
            extraction_note=draft.extraction_note,
        )

    def get_analysis(self, sketch_id: str) -> SketchAnalysisResponse | None:
        return self._analysis_store.get(sketch_id)


def _infer_extension(filename: str | None) -> str:
    if not filename:
        return ".png"
    suffix = Path(filename).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".png"


sketch_service = SketchService()
