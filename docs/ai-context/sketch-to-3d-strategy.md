# Sketch-to-3D Strategy (Phase A+)

## Goal
Deliver accurate ring reconstruction from sketch images with feature-aware customization bound to ring semantics.

## Assessment of Previous Approach
The earlier stack choice (SAM + GroundingDINO + parametric CAD graph) was directionally correct but incomplete for accuracy. It needs ring-specific feature prediction and CAD fitting optimization to close the gap between sketch intent and 3D geometry.

## Recommended Model Stack
1. Component proposal and localization:
- GroundingDINO (region proposals for band, center stone, side stones, setting/prongs)

2. Component masks:
- SAM 2 (refined segmentation per proposed component)

3. Ring feature heads (trained on synthetic CAD render dataset):
- center_stone_shape classifier
- setting style classifier
- prong count predictor
- band profile classifier
- scalar regressors (gem size prior, band thickness prior)

4. Optional depth prior (for ambiguity reduction):
- Marigold-style monocular depth prior for contour consistency guidance

5. Parametric CAD fit loop:
- optimize ring graph params to sketch evidence
- losses: silhouette overlap, contour edge distance, component consistency penalties

## Why This Fits Constraints
- CPU-safe demo path: deterministic fallback and cached model artifacts remain available.
- No paid dependency requirement: all recommended models can be used in open/offline workflows.
- Component-aware customization: extracted ring features map directly to ring graph fields.

## Phase Plan
### Phase A (implemented now)
- Sketch upload API
- Deterministic feature extraction baseline
- Feature-aware ring parameters in create/edit flow
- Feature-driven geometry variation in export mesh

### Phase B
- Introduce component proposal + mask inference service contracts.
- Persist intermediate component detections and confidences.
- Add confidence-gated UX prompts for uncertain features.

### Phase C
- Train/fine-tune ring-specific feature heads on synthetic CAD render corpus.
- Replace deterministic feature inference with learned predictors.

### Phase D
- Add CAD fitting optimization loop for sketch-to-geometry alignment.
- Add quantitative metrics: silhouette IoU, contour Chamfer, feature agreement.

## Accuracy Definition for MVP+
A reconstruction is considered acceptable when:
- predicted ring features match user-confirmed features,
- silhouette overlap and contour alignment exceed configured thresholds,
- customization edits preserve feature semantics in resulting geometry.
