# AGENTS.md

This file provides guidance for AI coding assistants working in this repository.

## Start Here (Required Context Reads)
Before making significant changes, read these files in order:
1. docs/ai-context/project-overview.md
2. docs/ai-context/architecture.md
3. docs/ai-context/constraints.md
4. docs/ai-context/roadmap.md
5. docs/ai-context/coding-guidelines.md

## Project Purpose
Build an AI-assisted jewelry system that converts design input into editable 3D ring models and supports fast component-level customization.

## Architecture Rules You Must Respect
- Preserve component-aware parametric CAD graph as the core model.
- Do not regenerate entire assets for small edits.
- Keep fast interactive edit loop separate from heavy generation/render jobs.
- Maintain MVP export support for GLB (viewer) and STL (manufacturing).

## MVP Reality and Scope
- Rings only.
- Single-user/local session mode.
- Required low-latency edits: materials, gemstone type, gemstone size, band thickness.
- Cost estimation and lightweight manufacturability checks are part of MVP.

## Environment and Performance Assumptions
- Dev may use GPU, but demo machines may be CPU-only.
- Live demo path must remain stable without heavy real-time inference.
- Precompute/cache expensive operations when possible.

## Tooling and Dependency Rules
- Prefer free/open and offline-capable solutions where practical.
- Do not use restricted tools: Tripo3D, fal.ai.
- Avoid introducing paid API dependencies in MVP.
- If a major architecture/tool change seems better, stop and ask for approval first.

## Implementation Process Rules
- Implement in small, well-defined tasks.
- Add logging and runnable test commands at each stage.
- Keep modules clean and expandable for future phases.
- Update docs/ai-context files when decisions or architecture change.

## Output Quality Expectations
- Outputs should be visually populated, not placeholder-only.
- Geometry and exports should aim for clean, valid artifacts suitable for intended stage usage.
- Prioritize interactive stability and predictable behavior in demo flow.
