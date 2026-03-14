from importlib.util import find_spec
from pathlib import Path

from app.services.sketch_analysis.base import SketchAnalysisDraft
from app.services.sketch_analysis.deterministic import DeterministicSketchAnalyzer
from app.services.sketch_analysis.grounded_sam_adapters import (
    AdapterInitializationError,
    FeatureHeadAdapter,
    ProposalAdapter,
    SegmentationAdapter,
    create_grounded_sam_adapters,
    decode_grayscale,
)


class ModelProviderUnavailableError(RuntimeError):
    pass


class GroundedSamSketchAnalyzer:
    """Scaffold for GroundingDINO + SAM2 provider.

    This class validates runtime prerequisites and keeps a deterministic fallback
    baseline for interface compatibility while model wiring is being implemented.
    """

    def __init__(
        self,
        device: str,
        grounding_dino_checkpoint_path: str | None,
        sam2_checkpoint_path: str | None,
        mode: str = "scaffold",
        grounding_dino_model_id: str = "IDEA-Research/grounding-dino-base",
        sam2_model_id: str = "facebook/sam2-hiera-large",
        grounding_dino_box_threshold: float = 0.25,
        grounding_dino_text_threshold: float = 0.25,
        grounding_dino_local_files_only: bool = True,
        proposal_adapter: ProposalAdapter | None = None,
        segmentation_adapter: SegmentationAdapter | None = None,
        feature_head_adapter: FeatureHeadAdapter | None = None,
    ) -> None:
        self._mode = mode
        self._device = device
        self._grounding_dino_checkpoint_path = grounding_dino_checkpoint_path
        self._sam2_checkpoint_path = sam2_checkpoint_path
        self._baseline = DeterministicSketchAnalyzer()
        self._grounding_dino_box_threshold = grounding_dino_box_threshold
        self._grounding_dino_text_threshold = grounding_dino_text_threshold
        self._grounding_dino_local_files_only = grounding_dino_local_files_only
        self._grounding_dino_model_id = grounding_dino_model_id
        self._sam2_model_id = sam2_model_id
        self._validate_runtime()
        if proposal_adapter and segmentation_adapter and feature_head_adapter:
            self._proposal_adapter = proposal_adapter
            self._segmentation_adapter = segmentation_adapter
            self._feature_head_adapter = feature_head_adapter
        else:
            try:
                built = create_grounded_sam_adapters(
                    mode=self._mode,
                    checkpoint_path_dino=self._grounding_dino_checkpoint_path or "",
                    checkpoint_path_sam2=self._sam2_checkpoint_path or "",
                    device=self._device,
                    grounding_dino_model_id=self._grounding_dino_model_id,
                    sam2_model_id=self._sam2_model_id,
                    grounding_dino_box_threshold=self._grounding_dino_box_threshold,
                    grounding_dino_text_threshold=self._grounding_dino_text_threshold,
                    grounding_dino_local_files_only=self._grounding_dino_local_files_only,
                )
            except AdapterInitializationError as err:
                raise ModelProviderUnavailableError(str(err)) from err

            self._proposal_adapter, self._segmentation_adapter, self._feature_head_adapter = built

    def analyze(self, content: bytes) -> SketchAnalysisDraft:
        baseline = self._baseline.analyze(content)
        grayscale = decode_grayscale(content)
        proposals = self._proposal_adapter.propose(grayscale)
        masks = self._segmentation_adapter.segment(grayscale, proposals)
        predicted = self._feature_head_adapter.predict(grayscale, masks, baseline)

        if not predicted.components:
            return baseline
        return predicted

    def _validate_runtime(self) -> None:
        missing = [
            dep
            for dep in ("torch", "transformers")
            if find_spec(dep) is None
        ]
        if missing:
            raise ModelProviderUnavailableError(
                "Grounded-SAM backend unavailable: missing dependencies "
                f"{', '.join(missing)}"
            )

        if not self._grounding_dino_checkpoint_path or not self._sam2_checkpoint_path:
            raise ModelProviderUnavailableError(
                "Grounded-SAM backend unavailable: checkpoint paths are not configured"
            )

        if not Path(self._grounding_dino_checkpoint_path).exists():
            raise ModelProviderUnavailableError(
                "Grounded-SAM backend unavailable: grounding dino checkpoint path does not exist"
            )

        if not Path(self._sam2_checkpoint_path).exists():
            raise ModelProviderUnavailableError(
                "Grounded-SAM backend unavailable: sam2 checkpoint path does not exist"
            )
