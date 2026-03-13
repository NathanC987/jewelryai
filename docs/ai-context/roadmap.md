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

## Phase 1: End-to-End MVP Loop (Target first working demo)
Primary objective:
- Demonstrate ring workflow from sketch input to editable 3D + exports.

Scope:
- Sketch upload path as first-class input.
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

2. Style presets
- Add style transforms through parameter sets (minimalist, vintage, royal, etc.).

3. Catalog image generation
- Add predefined render scenes/background pipelines.

4. Manufacturability rule expansion
- Add richer checks and clearer diagnostics.

## Phase 4: Extended Input and Output Coverage
- Add text prompt as first-class generation path.
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
