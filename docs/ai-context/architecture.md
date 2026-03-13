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
- Accept user input (MVP priority: sketch upload).
- Show interactive 3D model (GLB) with camera controls.
- Expose editing controls for materials, gemstones, and key dimensions.
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

Responsibilities:
- Build ring geometry from structured parameters.
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

## Architecture Rules to Preserve
- No full AI regeneration per small edit.
- Respect component-aware parametric editing model.
- Keep live demo path CPU-safe.
- Separate fast interactive path from heavy generation/render jobs.
