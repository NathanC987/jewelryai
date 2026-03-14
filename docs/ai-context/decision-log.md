# Decision Log

## 2026-03-13

### D-001: MVP scope lock
- Decision: Rings only, single-user/local session mode.
- Reason: Maximize delivery confidence and stability for first demo.

### D-002: Export contract for MVP
- Decision: Support GLB (web visualization) and STL (manufacturing) first.
- Reason: Meets viewer and manufacturing requirements while controlling scope.

### D-003: Interaction strategy
- Decision: Target 200 ms to 1 s for material swap, gemstone type, gemstone size, and band thickness edits via parametric updates.
- Reason: Core judging priority is fast interactive customization.

### D-004: Rendering split
- Decision: Use fast Three.js PBR for interactive updates and Blender/Cycles for high-quality asynchronous outputs.
- Reason: Maintains responsiveness on CPU-only demo systems while preserving render quality path.

### D-005: Implementation sequencing
- Decision: Strict phased rollout, implementing modular services in small validated steps.
- Reason: Required by project constraints and delivery timeline.

### D-006: Phase 0 module layout execution
- Decision: Implement monorepo-style baseline with apps/backend, apps/frontend, and packages/shared-schemas before domain logic.
- Reason: Preserves modularity and allows independent evolution of gateway, UI, and shared contracts while keeping Phase 1 implementation fast.

### D-007: Deterministic local ring state service first
- Decision: Implement ring customization API on top of an in-memory parametric ring graph before wiring persistent storage and full CAD kernels.
- Reason: Enables immediate end-to-end interaction and validation of edit contracts, latency behavior, and cost/warning outputs without blocking on heavier infrastructure.

### D-008: API-first customization workbench integration
- Decision: Connect frontend customization controls directly to backend create/patch ring APIs before introducing 3D geometry rendering integration.
- Reason: Verifies the critical interaction contract and low-latency edit loop early, reducing risk before CAD and viewer complexity is added.

### D-009: Placeholder Three.js preview before GLB pipeline
- Decision: Add a lightweight Three.js placeholder ring visualization as an interim viewer step before backend-generated GLB streaming.
- Reason: Keeps UI architecture aligned with final viewer flow while backend CAD/export paths are still under implementation.

### D-010: MVP export endpoints before CAD exporter wiring
- Decision: Implement GLB/STL API contract endpoints now with deterministic artifact URI responses, deferring full CAD file generation integration.
- Reason: Locks the output API early so frontend flow and downstream wiring can proceed independently of CAD kernel/export engine completion.

### D-011: Frontend container runs as host UID/GID
- Decision: Configure Docker Compose frontend service to run as host user IDs on Linux.
- Reason: Prevents root-owned .next and related permission failures during local non-container frontend runs.

### D-012: Versioned ring CAD graph API in MVP backend
- Decision: Implement a deterministic in-memory CAD graph representation with explicit nodes/edges, graph versioning, and update diffs returned by ring edit APIs.
- Reason: Establishes the component-aware editing contract required by architecture and enables future CAD/export engine replacement without breaking API behavior.

### D-013: Generate export artifacts with procedural mesh backend
- Decision: Replace export URI-only stubs by generating actual STL and GLB files from deterministic procedural ring meshes (band + center stone) and serve them via static /artifacts.
- Reason: Provides real downloadable/viewable artifacts for MVP output validation while preserving a lightweight CPU-safe pipeline ahead of full CAD kernel integration.

### D-014: Frontend viewer consumes backend-origin GLB assets
- Decision: Wire the frontend viewer to request and load backend-generated GLB artifacts using absolute backend URLs, with a placeholder fallback model when loading is unavailable.
- Reason: Eliminates origin mismatch/404 behavior from frontend-host-relative artifact paths and establishes a stable end-to-end visualization loop for create/edit flows.

### D-015: Always regenerate exports from latest ring parameters
- Decision: Rebuild GLB/STL artifacts on export requests from current ring parameters and expand procedural geometry mapping to include band dimensions, gemstone-type variation, and prong hints.
- Reason: Prevents stale artifact reuse after ring edits and makes exported/viewed geometry respond clearly to MVP customization controls.

### D-016: Add lightweight required-edit latency benchmark API
- Decision: Add a backend benchmark endpoint that executes material, gemstone type, gemstone size, and band thickness updates over configurable iterations and reports min/avg/max latency per operation against a target max threshold.
- Reason: Provides repeatable validation for MVP edit-latency goals without introducing heavyweight performance tooling.

### D-017: Add sketch ingestion with deterministic seed extraction
- Decision: Introduce a sketch upload API that persists image artifacts and derives deterministic seed ring parameters (metal, gemstone type/size, band thickness) used to initialize ring creation in the frontend.
- Reason: Establishes a concrete input-to-3D bridge in MVP flow now, while full AI concept/extraction stages are still under implementation.

### D-018: Adopt feature-aware sketch-to-3D pipeline strategy
- Decision: Keep component-aware CAD graph core, and move toward GroundingDINO + SAM2 + ring-specific feature heads + CAD fitting optimization for accurate sketch reconstruction.
- Reason: The prior generic extraction direction is useful but insufficient alone for accuracy; feature-level inference and fitting are required for reliable sketch-to-3D mapping and feature-based customization.

### D-019: Add stable sketch analysis API boundary before model swap
- Decision: Add a sketch analysis endpoint returning component detections, feature confidence scores, and a user-confirmation flag while keeping deterministic internals for now.
- Reason: Establishes a stable contract for later GroundingDINO/SAM2 integration and enables confidence-aware UX without repeatedly changing frontend/backend interfaces.

### D-020: Introduce sketch-analysis provider abstraction with config switching
- Decision: Refactor sketch analysis internals behind a provider interface and support runtime backend selection via SKETCH_ANALYSIS_BACKEND while keeping upload/analysis API schema unchanged.
- Reason: Enables safe iteration from deterministic baseline to model-backed inference (mock then production providers) without frontend or contract churn.

### D-021: Add grounded_sam provider scaffold with safe fallback
- Decision: Add a GroundingDINO/SAM2 provider scaffold that validates runtime dependencies/checkpoint config and falls back to configured backend when unavailable.
- Reason: Establishes production integration path immediately while preserving reliable local/demo operation before heavy model assets are wired.

### D-022: Implement grounded_sam internal adapter boundaries
- Decision: Define proposal, segmentation, and feature-head adapter contracts inside grounded_sam provider and route analyze() through this pipeline with scaffold implementations.
- Reason: Makes real model integration incremental and testable without changing service or API interfaces.

### D-023: Add grounded_sam real-mode wiring with guarded fallback
- Decision: Introduce real-mode adapter selection and model-id configuration, while retaining deterministic fallback if dependencies/checkpoints/runtime constraints are not met.
- Reason: Enables progressive activation of real inference on capable machines without destabilizing default local/demo workflows.

### D-024: Execute GroundingDINO proposals in real mode with offline-safe loading
- Decision: Implement real GroundingDINO proposal execution in the real adapter using transformers runtime, normalize/deduplicate component proposals, and keep deterministic proposal fallback when inference returns no usable detections.
- Reason: Moves sketch analysis from pure scaffold toward genuine model-driven component detection while preserving stable behavior on machines without cached models or complete runtime assets.

### D-025: Add rule-based style variation generation for demo impact
- Decision: Implement a ring variation endpoint that generates five style preset concepts (Minimalist, Vintage, Royal, Modern, Bold) from a source ring and wire it into the frontend workbench with one-click activation.
- Reason: Delivers a high-impact, roadmap-aligned capability that makes the MVP materially more impressive for demos without introducing heavy runtime dependencies.

### D-026: Add hybrid feature-to-geometry coherence pass for ring settings
- Decision: Promote setting height to a first-class inferred/editable parameter and update mesh generation to build a coherent setting basket with angled prongs fitted around the center stone.
- Reason: Improves geometric coherence and sketch resemblance immediately while preserving component-aware parametric editability and low-latency updates.

### D-027: Immediate release pivot to prompt-first template generation
- Decision: Make prompt-first deterministic interpretation into parametric ring templates the default MVP generation path, while retaining sketch upload as an experimental seed/fidelity track.
- Reason: Produces more consistent polished initial outputs in the current release window, aligns with RhinoArtisan-style methodology, and preserves component-aware local edits without full regeneration.

### D-028: Adopt internal/open component library assembly path
- Decision: Implement exporter-side assembly from an internal/open reusable component catalog (bands, settings, accents, stones/prongs) instead of relying on a single monolithic procedural generator.
- Reason: Improves output consistency and aesthetic coherence while keeping the architecture license-safe, offline-capable, and compatible with localized parametric edits.
