# Roadmap

## Delivery Strategy
Use a strict phased approach with a stable MVP first, then incremental expansion.

## Phase 0: Foundation and Skeleton (Immediate)
Goals:
- Establish modular monorepo/service structure.
- Set up frontend shell, backend API skeleton, and shared schema contracts.
- Add baseline logging, health checks, and test command scaffolding.

Outputs:
- Running frontend + backend containers.
- Basic API contract docs and placeholder endpoints.
- CI/test command stubs for each service.

Progress snapshot (2026-03-13):
- Completed:
	- Modular repository skeleton created.
	- Backend FastAPI gateway scaffold with structured logging and smoke test.
	- Deterministic ring create/get/update API with in-memory parametric state.
	- Frontend Next.js shell with MVP control placeholders.
	- Frontend workbench wired to backend ring edit APIs.
	- Three.js center-panel placeholder viewer added.
	- GLB/STL export contract endpoints and UI request actions added.
	- Deterministic CAD graph model with graph endpoint and versioned update diffs added.
	- Real generated STL/GLB artifacts now produced and served via backend /artifacts.
	- Frontend viewer now loads backend-generated GLB artifacts with placeholder fallback.
	- Frontend workbench now resolves backend-origin artifact URLs for viewer refresh and export links.
	- Export mesh fidelity improved with parameter-aware geometry updates for ring edits.
	- Export artifacts now regenerate from latest ring parameters on each export request.
	- Lightweight edit latency benchmark API added for required MVP operations.
	- Sketch upload ingestion endpoint added with deterministic parameter extraction.
	- Frontend now seeds ring creation from uploaded sketch extraction output.
	- Feature-aware ring parameters added (stone shape, prong count, band profile) and exposed in customization UI.
	- Export geometry now updates from feature-level ring edits, not only scalar size/thickness edits.
	- Sketch analysis contract added with component detections and feature confidence outputs for future model integration.
	- Sketch analysis provider abstraction added with config-based backend swapping (deterministic/mock_model) under stable API contracts.
	- Added grounded_sam provider scaffold with runtime availability checks and automatic fallback routing.
	- Added grounded_sam adapter pipeline scaffolding (proposal/segmentation/feature-head contracts) with test coverage.
	- Added real-mode adapter wiring path and config toggles, with safe fallback behavior when runtime/model assets are unavailable.
	- GroundingDINO real-mode proposal inference now executes in adapter pipeline with normalized/deduplicated component outputs and deterministic fallback.
	- Rule-based design variation generator added with five style presets and frontend activation workflow.
	- Viewer controls and UI polish improved with interactive orbit controls and neutral monochrome styling.
	- Shared ring parameter JSON schema and root run/test commands.
- Next in sequence:
	- Refine prompt interpreter quality and expand template library coverage.

## Phase 1: End-to-End MVP Loop (Target first working demo)
Primary objective:
- Demonstrate ring workflow from prompt input to editable 3D + exports.

Scope:
- Prompt-first path as first-class input.
- Sketch upload retained as experimental seed mode.
- Structured ring CAD graph generation.
- Real-time edits for materials, gemstone type/size, band thickness.
- GLB viewer updates in Three.js.
- STL export.
- Cost estimate + lightweight manufacturability warnings.

Performance target:
- 200 ms to 1 s for required edit operations.

Stability target:
- CPU-safe live demo path, no dependence on heavy on-demand inference.

## Phase 2: Quality and UX Hardening
Goals:
- Improve visual realism in interactive viewer materials.
- Add Blender/Cycles final render pipeline with queued jobs.
- Improve extraction robustness and fallback heuristics.
- Expand test coverage for geometry validity and API reliability.

## Phase 3: High-Impact Extras (Prioritized)
1. Design variations generator
- Implement rule-based parametric generation of 5 variants.
 - Status: Completed in MVP demo path.

2. Style presets
- Add style transforms through parameter sets (minimalist, vintage, royal, etc.).

3. Catalog image generation
- Add predefined render scenes/background pipelines.

4. Manufacturability rule expansion
- Add richer checks and clearer diagnostics.

## Phase 4: Extended Input and Output Coverage
- Expand sketch/reference-image fidelity track (inverse fitting + stronger segmentation).
- Add reference image pipeline improvements.
- Add additional CAD/export formats (for example STEP) when core loop is stable.

## Phase 5: Future Exploration
- AR try-on implementation.
- Optional natural-language edit parsing.
- Multi-user/project collaboration and authentication.

## Suggested Milestone Gates
Gate A:
- End-to-end loop works with deterministic sample input.

Gate B:
- Real-time edits stay in target latency under demo conditions.

Gate C:
- Exported STL passes basic geometry sanity checks.

Gate D:
- Cost/manufacturability output is consistent with parameter changes.
