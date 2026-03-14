from app.services.sketch_analysis.base import SketchAnalyzer
from app.services.sketch_analysis.deterministic import DeterministicSketchAnalyzer
from app.services.sketch_analysis.grounded_sam import (
    GroundedSamSketchAnalyzer,
    ModelProviderUnavailableError,
)
from app.services.sketch_analysis.mock_model import MockModelSketchAnalyzer


def create_sketch_analyzer(
    backend: str,
    *,
    fallback_backend: str = "deterministic",
    allow_fallback: bool = True,
    device: str = "cpu",
    grounded_sam_mode: str = "scaffold",
    grounding_dino_model_id: str = "IDEA-Research/grounding-dino-base",
    sam2_model_id: str = "facebook/sam2-hiera-large",
    grounding_dino_box_threshold: float = 0.25,
    grounding_dino_text_threshold: float = 0.25,
    grounding_dino_local_files_only: bool = True,
    grounding_dino_checkpoint_path: str | None = None,
    sam2_checkpoint_path: str | None = None,
) -> tuple[SketchAnalyzer, str]:
    if backend == "deterministic":
        return DeterministicSketchAnalyzer(), "deterministic"
    if backend == "mock_model":
        return MockModelSketchAnalyzer(), "mock_model"
    if backend == "grounded_sam":
        try:
            return (
                GroundedSamSketchAnalyzer(
                    device=device,
                    mode=grounded_sam_mode,
                    grounding_dino_model_id=grounding_dino_model_id,
                    sam2_model_id=sam2_model_id,
                        grounding_dino_box_threshold=grounding_dino_box_threshold,
                        grounding_dino_text_threshold=grounding_dino_text_threshold,
                        grounding_dino_local_files_only=grounding_dino_local_files_only,
                    grounding_dino_checkpoint_path=grounding_dino_checkpoint_path,
                    sam2_checkpoint_path=sam2_checkpoint_path,
                ),
                "grounded_sam",
            )
        except ModelProviderUnavailableError:
            if allow_fallback:
                return create_sketch_analyzer(
                    fallback_backend,
                    fallback_backend=fallback_backend,
                    allow_fallback=False,
                    device=device,
                    grounded_sam_mode=grounded_sam_mode,
                    grounding_dino_model_id=grounding_dino_model_id,
                    sam2_model_id=sam2_model_id,
                    grounding_dino_box_threshold=grounding_dino_box_threshold,
                    grounding_dino_text_threshold=grounding_dino_text_threshold,
                    grounding_dino_local_files_only=grounding_dino_local_files_only,
                    grounding_dino_checkpoint_path=grounding_dino_checkpoint_path,
                    sam2_checkpoint_path=sam2_checkpoint_path,
                )
            raise
    raise ValueError(f"Unsupported sketch analysis backend: {backend}")
