# Constraints and Decisions

## Hard Product Constraints
- Problem scope: AI-driven 2D to 3D jewelry workflow with real-time customization.
- MVP jewelry scope: Rings only.
- MVP session mode: Single-user local mode.
- MVP exports: GLB (visualization) and STL (manufacturing).
- Real-time target for key edits: 200 ms to 1 s.

## Required Low-Latency Edit Types (MVP)
- Material swap.
- Gemstone type swap.
- Gemstone size adjustment.
- Band thickness adjustment.

## Quality and Validity Constraints
- Initial output should be visually populated (no empty base placeholders).
- 3D outputs should be clean and watertight for intended use.
- Manufacturability in MVP is lightweight/hybrid checks, not full CAD-grade verification.

## Platform and Tooling Constraints
- Avoid paid APIs where possible.
- Prefer free/open models and tools.
- Offline-capable operation is preferred.
- Restricted tools/APIs: Tripo3D and fal.ai (explicitly disallowed).

## Demo Environment Constraints
- Development may use RTX 4070.
- Demo expected on laptops without discrete GPU.
- Therefore, live demo must avoid heavy real-time inference and depend on CPU-safe interactive paths.
- Heavy AI and photoreal stages should be precomputed/cached or asynchronous.

## Scope and Sequencing Constraints
- Strict phased rollout is required.
- Do not implement all features at once.
- Build in smaller well-defined tasks with validation at each stage.
- Keep codebase modular and expandable for future features.

## Architecture Constraints (Must Preserve)
- Component-aware parametric model is mandatory.
- Avoid full pipeline regeneration for small edits.
- Avoid relying solely on generic mesh segmentation or generic part decomposition.
- Maintain separate paths for:
  - fast interactive updates
  - heavy rendering/generation jobs

## Process Constraints from Team
- Add proper logging at each stage.
- Add testing commands/checks at each stage.
- If a better tool/approach appears during implementation, discuss before switching.

## Deferred or Later-Phase Items
- AR try-on is roadmap-only for now.
- Natural language edit parsing is deferred; direct UI controls first.
- Additional exports beyond GLB/STL (for example OBJ/STEP) are deferred to later phases.
