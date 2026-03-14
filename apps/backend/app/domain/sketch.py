from pydantic import BaseModel

from app.domain.ring import RingParameters


class ComponentDetection(BaseModel):
    component_type: str
    bbox_norm_xywh: list[float]
    confidence: float


class FeatureConfidence(BaseModel):
    feature_name: str
    value: str | float | int
    confidence: float


class SketchAnalysisResponse(BaseModel):
    sketch_id: str
    artifact_uri: str
    analysis_backend: str
    components: list[ComponentDetection]
    extracted_parameters: RingParameters
    feature_confidences: list[FeatureConfidence]
    requires_user_confirmation: bool


class SketchUploadResponse(BaseModel):
    sketch_id: str
    artifact_uri: str
    analysis_uri: str
    analysis_backend: str
    extracted_parameters: RingParameters
    extraction_note: str
