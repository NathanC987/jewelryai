# System Architecture

## High-Level Pipeline
User (Web App)
-> Prompt/Sketch/Reference Input
-> AI Design Generator (2D concept)
-> Geometry Extraction Engine
-> Parametric CAD Builder (structured model)
-> Parametric Editing Engine (component-level updates)
-> Rendering Engine
-> Manufacturing + Cost Engine
-> 3D Viewer + Export

## Frontend Layer
Stack:
- Next.js + React
- Three.js viewer

Responsibilities:
- Accept user input (MVP priority: prompt-first ring generation).
- Keep sketch upload available as an experimental seed flow.
- Show interactive 3D model (GLB) with camera controls.
- Expose editing controls for materials, gemstones, and key dimensions.
- Require user confirmation for low-confidence extracted sketch features before seeded 3D generation.
- Display cost estimate and manufacturability warnings.
- Trigger export actions (GLB visualization artifact, STL manufacturing file).

## Backend Gateway Layer
Stack:
- FastAPI
- Redis + Celery for background jobs

Responsibilities:
- Provide API endpoints for generation, customization, rendering requests, checks, and exports.
- Coordinate synchronous low-latency edit operations vs asynchronous heavy jobs.
- Route data between model services, CAD service, render service, and persistence.
- Operate in single-user/local session mode for MVP.

## AI Design Service
Stack discussed:
- Stable Diffusion XL
- ControlNet
- Diffusers

Responsibilities:
- Convert user design intent into a clean 2D jewelry concept image.
- In MVP demo safety mode, heavy generation should be precomputed/cached when possible.

## Geometry Extraction Service
Stack discussed:
- Segment Anything (SAM)
- GroundingDINO
- Shape/geometry heuristics

Responsibilities:
- Detect likely jewelry regions/components from 2D concept.
- Produce structured extraction output for CAD construction.
- Avoid relying on mesh segmentation alone as a sole strategy.
- Evolve toward ring-specific feature prediction (stone shape, setting style, prong count, band profile) used by parametric CAD graph.
- Hybrid refinement step in progress: sketch-derived feature priors now drive setting-height and coherent prong placement in procedural geometry.
- Grounded-SAM scaffold provider now defines adapter boundaries:
  - proposal adapter (GroundingDINO contract)
  - segmentation adapter (SAM2 contract)
  - feature head adapter (ring-feature prediction contract)

Reference:
- docs/ai-context/sketch-to-3d-strategy.md

Example structured output (illustrative):
```json
{
  "band_radius_mm": 9,
  "center_stone_shape": "oval",
  "side_stone_count": 12,
  "prong_count": 4
}
```

## Parametric CAD Service (Core)
Stack discussed:
- OpenCascade (kernel)
- CadQuery (Python layer)
- Internal/open reusable component library (assembly catalog)

Responsibilities:
- Build ring geometry from structured parameters.
- Assemble ring models from reusable CAD components (band, setting, accents, stone/prong modules) selected from internal/open catalog.
- Maintain component-aware graph for targeted edits.
- Rebuild only affected nodes on changes (not full regeneration).
- Produce exports required by MVP (GLB pipeline asset + STL manufacturing export).

## Internal Representation: CAD Graph
Representative structure:
- Ring
- Band
- Center stone
- Side stones
- Prongs/settings

Why this matters:
- Enables low-latency partial updates.
- Preserves design semantics for customization, validation, and pricing.

## Parametric Editing Engine
Responsibilities:
- Apply user edits directly to graph parameters.
- Recompute only impacted geometry components.
- Return updated mesh/model payload quickly for viewer refresh.

MVP decision:
- Direct UI controls first.
- Natural language edit parsing (for example via LLM) is deferred.

## Rendering and Visualization
Interactive path:
- Three.js PBR materials for responsive edits.

High-quality path:
- Headless Blender + Cycles for photoreal outputs.

Responsibilities:
- Keep interactive path fast and stable.
- Offload slower photoreal rendering to background jobs.

## Manufacturing + Cost Engine
Responsibilities:
- Compute metal weight from CAD-derived volume and density tables.
- Compute gemstone estimates from type/size rules.
- Return approximate price and line-item breakdown.
- Run lightweight manufacturability checks in MVP:
  - minimum thickness heuristics
  - basic stability checks
  - sanity checks for invalid geometry conditions

## Data and Storage
Stack discussed:
- PostgreSQL
- Redis
- MinIO or S3-compatible object storage

Responsibilities:
- Store project metadata/parameters.
- Cache repeated AI/render/CAD results.
- Store artifacts: renders, meshes, and export files.

## Infrastructure
- Containerization: Docker
- Orchestration for MVP: Docker Compose
- Future scale path: Kubernetes (later phase)

## Current Implemented Modules (Phase 0)
- Backend gateway skeleton at apps/backend:
  - FastAPI app bootstrap and versioned API prefix (/api/v1)
  - Health route and placeholder projects route
  - Ring routes for create/get/update and graph inspection in single-user local mode
  - Sketch upload route with deterministic preprocessing into seed ring parameters
  - Sketch analysis route exposing component detections and feature confidence outputs
  - Sketch analysis grounded_sam real mode now executes GroundingDINO proposal inference with normalized/deduplicated component proposals and deterministic fallback when detections are unavailable
  - GroundingDINO real inference tuning via settings: box threshold, text threshold, and local-files-only offline loading
  - Feature-aware ring parameters (stone shape, prong count, band profile) in create/update flow
  - Side-stone count promoted to first-class ring parameter, driven from sketch extraction and UI edits
  - Setting-height promoted to first-class ring parameter and used to fit a coherent stone/prong assembly
  - Benchmark route for required edit latency checks (material/gemstone size/type/band thickness)
  - Ring variation route that generates style-based concept variants from a source ring for rapid exploration
  - Export routes for GLB/STL artifact generation
  - In-memory ring graph service with deterministic cost/manufacturability outputs
  - Graph versioning and update diffs (changed fields + impacted components)
  - Parameter-aware procedural export mesh (band, center stone, and prongs)
  - Export mesh now responds to feature-level ring params (shape/profile/prong count/side-stone count/setting height)
  - Prompt interpreter service and /rings/from-prompt endpoint for deterministic prompt-to-template initialization
  - Ring change-prompt endpoint (/rings/{id}/change-prompt) for deterministic natural-language component swaps
  - Open component library assembly path used by exporter to compose ring models from reusable parts
  - Local component ingestion path from repository-level /components library (baskets/pegheads/bezels/halos/clusters/shanks) with procedural fallback
  - Component catalog manifest support added for curated file-backed component overrides with automatic procedural fallback
  - Prompt interpretation now returns selected component recipe IDs for assembly transparency
  - Export mesh now responds to template/style identity (solitaire/halo/pave/split-shank/three-stone + style tags)
  - Prong geometry now uses coherent angled supports around the center stone instead of simple vertical pegs
  - Export regeneration on each request to reflect latest ring parameter updates
  - Structured request logging middleware
  - Pytest smoke test setup
- Frontend shell at apps/frontend:
  - Next.js app router skeleton
  - Three-panel layout scaffold (input/viewer/customization)
  - Prompt-first ring generation workflow as default entry path
  - Sketch upload input with local preview and backend ingestion trigger
  - Sketch path retained as experimental seed mode
  - Sketch analysis confidence panel for feature-level user confirmation
  - Three.js viewer with backend GLB loading and placeholder fallback
  - API-backed ring workbench control panel
  - Prompt interpretation feedback panel (template/style/confidence)
  - Ring creation seeded from extracted sketch parameters
  - Ring creation from prompt-backed template interpretation
  - Sketch feature confirmation workflow before seeding ring creation when confidence is low
  - In-workbench generation of five style variations with one-click variant activation
  - Live create/patch flow for metal, gemstone type/size, and band thickness
  - Backend-origin artifact URL handling for viewer and export links
- Shared contracts at packages/shared-schemas:
  - ring-parameters schema for material/gemstone/size edits
- Root orchestration:
  - docker-compose baseline for backend and frontend services
  - Makefile command shortcuts for run/test/lint

- Artifact serving:
  - Backend mounts static /artifacts path for generated export retrieval.

## Architecture Rules to Preserve
- No full AI regeneration per small edit.
- Respect component-aware parametric editing model.
- Keep live demo path CPU-safe.
- Separate fast interactive path from heavy generation/render jobs.
