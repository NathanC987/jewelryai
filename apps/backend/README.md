# Backend Gateway

FastAPI gateway for MVP orchestration.

## Run
1. Create environment and install dependencies.
2. Start API server:
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Test
- uv run pytest -q

## Edit Latency Benchmark
- Run benchmark API for required MVP edit operations:
   - curl "http://localhost:8000/api/v1/benchmarks/edits?iterations=20"
- Response includes per-operation min/avg/max latency and pass/fail against configured target max milliseconds.

## Sketch Upload (Feature Seed)
- Upload sketch image:
   - curl -F "file=@ring-sketch.png" "http://localhost:8000/api/v1/sketches/upload"
- Response returns stored sketch artifact URI plus extracted feature-aware ring seed parameters:
   - metal, gemstone_type, center_stone_shape, prong_count, band_profile, gemstone_size_mm, band_thickness_mm

## Sketch Analysis Backend Selection
- Configure provider via environment variable:
   - SKETCH_ANALYSIS_BACKEND=deterministic (default)
   - SKETCH_ANALYSIS_BACKEND=mock_model
   - SKETCH_ANALYSIS_BACKEND=grounded_sam (scaffold; falls back by default if unavailable)
- Fallback controls:
   - SKETCH_ANALYSIS_ALLOW_FALLBACK=true|false
   - SKETCH_ANALYSIS_FALLBACK_BACKEND=deterministic|mock_model
- Grounded-SAM scaffold settings:
   - SKETCH_ANALYSIS_DEVICE=cpu|cuda
   - SKETCH_ANALYSIS_GROUNDED_SAM_MODE=scaffold|real
   - GROUNDING_DINO_MODEL_ID=<transformers model id>
   - GROUNDING_DINO_BOX_THRESHOLD=0.25
   - GROUNDING_DINO_TEXT_THRESHOLD=0.25
   - GROUNDING_DINO_LOCAL_FILES_ONLY=true|false
   - SAM2_MODEL_ID=<model id placeholder>
   - GROUNDING_DINO_CHECKPOINT_PATH=/path/to/checkpoint
   - SAM2_CHECKPOINT_PATH=/path/to/checkpoint
- API contracts remain unchanged when switching providers.

## Design Variations (Style Presets)
- Generate five style concepts from an existing ring:
   - curl -X POST "http://localhost:8000/api/v1/rings/{ring_id}/variations?count=5"
- Response returns style-labeled suggestions with full ring states that can be directly activated in the frontend workbench.

## Prompt-First Ring Generation (Default)
- Generate a ring directly from a design prompt:
   - curl -X POST "http://localhost:8000/api/v1/rings/from-prompt" -H "Content-Type: application/json" -d '{"prompt":"A vintage oval halo ruby ring in rose gold"}'
- Response includes:
   - deterministic interpretation (normalized prompt, template_id, style_tag, confidence)
   - selected component recipe IDs used for assembly (for example band.*, setting.*, style.*, accent.*)
   - full editable ring state initialized from template defaults
