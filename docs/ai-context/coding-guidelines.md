# Coding Guidelines

## Core Engineering Principles
- Prioritize modular boundaries so services/features can scale independently.
- Prefer deterministic, debuggable pipelines for MVP over opaque complexity.
- Keep the fast interactive loop separate from heavy asynchronous jobs.
- Never trigger full regeneration for small user edits when a component-level update is possible.

## Project Structure Expectations
- Separate concerns clearly:
  - frontend (UI/viewer)
  - backend gateway (API/orchestration)
  - AI generation/extraction services
  - CAD/parametric engine
  - rendering service
  - manufacturing/cost engine
- Use shared typed contracts/schemas for data passed between services.

## Coding Conventions
- Keep functions/services single-responsibility where possible.
- Favor explicit names for geometry parameters and units (for example mm, ct, g).
- Validate inputs early and return actionable error messages.
- Add comments only where logic is non-obvious.

## Logging Requirements
- Add structured logs at all service boundaries.
- Minimum fields per request/job log:
  - request_id or job_id
  - operation name
  - elapsed time
  - status
  - failure reason (when applicable)
- Log parameter diffs for edit operations (before/after summaries) without excessive payload noise.

## Testing and Validation Requirements
At each implementation stage, include runnable checks.

Expected categories:
- Unit tests:
  - parameter transforms
  - cost calculations
  - manufacturability rule checks
- Integration tests:
  - API to CAD graph update flow
  - export pipeline (GLB/STL existence and basic validity)
- Performance checks:
  - edit latency for required operations

## Stage-by-Stage Test Command Policy
Every stage should include explicit commands in docs/README for:
- backend tests
- frontend tests
- integration checks
- optional benchmark command for edit latency

If a stage does not yet support full tests, add minimal smoke tests and TODO markers for expansion.

## Dependency and Tooling Rules
- Prefer free/open and offline-capable tools where practical.
- Do not introduce paid API dependencies into MVP path.
- Do not use restricted tools (Tripo3D, fal.ai).
- If proposing a major tool/approach change, pause and get approval before implementation.

## Performance and Reliability Guidelines
- Cache expensive operations aggressively when safe.
- Keep demo path CPU-safe for live operation.
- Make asynchronous jobs retry-safe and idempotent when possible.
- Ensure failures in heavy jobs do not block interactive editing.

## Documentation Discipline
- Update ai-context docs whenever major decisions change.
- Keep architecture, constraints, and roadmap aligned with implementation reality.
