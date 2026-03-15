# JewelryAI

Modular MVP for AI-assisted ring generation and real-time customization.

## Team and Problem Statement
- Team Name: YoungMonks
- PS Title: AI-Driven 2D to 3D Jewelry Generation with Real-Time Customization (PS-01)

## Repository Layout
- apps/backend: FastAPI gateway and orchestration skeleton
- apps/frontend: Next.js UI and viewer shell
- packages/shared-schemas: cross-service data contracts
- docs/ai-context: persistent project memory and decisions

## Phase 0 Status
- Modular skeleton created.
- Backend API health route and structured request logging added.
- Frontend shell and customization panel placeholders added.
- Shared ring parameter schema added.
- Sketch upload to feature-aware ring seed flow is implemented.
- Ring create/update/export loop with live GLB refresh and STL output is implemented.

## Run (Local, no Docker)
Backend:
1. cd apps/backend
2. pip install uv
3. uv sync --dev
4. uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Frontend:
1. cd apps/frontend
2. npm install
3. npm run dev

## Run (Docker Compose)
- docker compose up --build

Linux note:
- To avoid root-owned frontend artifacts on bind mounts, run Docker Compose with user IDs exported:
	- export UID=$(id -u)
	- export GID=$(id -g)
	- docker compose up --build

## Test Commands
Backend unit/smoke tests:
- cd apps/backend && uv run pytest -q

Backend edit latency benchmark:
- curl "http://localhost:8000/api/v1/benchmarks/edits?iterations=20"

Frontend lint:
- cd apps/frontend && npm run lint

Fast demo readiness check:
- make demo-check

## Two-Hour Push Checklist
1. Run backend and frontend locally.
2. Upload one sketch and create ring from extracted parameters.
3. Confirm extracted sketch features (especially low-confidence fields) before creating the seeded ring.
4. Perform required live edits: metal, gemstone type/size, band thickness, shape/prong/profile, and side stone count.
5. Export GLB and STL from chosen design.
6. Run make demo-check before final push.

## Important Project Context
Read these files first before significant work:
- docs/ai-context/project-overview.md
- docs/ai-context/architecture.md
- docs/ai-context/constraints.md
- docs/ai-context/roadmap.md
- docs/ai-context/coding-guidelines.md
