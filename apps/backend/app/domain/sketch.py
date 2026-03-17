from typing import Literal

from pydantic import BaseModel, Field

from app.domain.ring import RingParameters


class ComponentDetection(BaseModel):
    component_type: str
    bbox_norm_xywh: list[float]
    confidence: float


class FeatureConfidence(BaseModel):
    feature_name: str
    value: str | float | int
    confidence: float


class SketchComponentMapping(BaseModel):
    source: Literal["known_filename", "deterministic_fallback", "vision_model"]
    confidence: float = Field(ge=0.0, le=1.0)
    matched_filename: str | None = None
    shank_component_id: str | None = None
    setting_component_id: str | None = None


class SketchAnalysisResponse(BaseModel):
    sketch_id: str
    artifact_uri: str
    analysis_backend: str
    components: list[ComponentDetection]
    extracted_parameters: RingParameters
    feature_confidences: list[FeatureConfidence]
    requires_user_confirmation: bool
    component_mapping: SketchComponentMapping | None = None


class SketchUploadResponse(BaseModel):
    sketch_id: str
    artifact_uri: str
    analysis_uri: str
    analysis_backend: str
    extracted_parameters: RingParameters
    extraction_note: str
    component_mapping: SketchComponentMapping | None = None
