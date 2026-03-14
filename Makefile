.PHONY: backend-run backend-test frontend-run frontend-lint demo-check up

backend-run:
	cd apps/backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	cd apps/backend && uv run pytest -q

frontend-run:
	cd apps/frontend && npm run dev

frontend-lint:
	cd apps/frontend && npm run lint

demo-check:
	cd apps/backend && uv run pytest -q
	cd apps/frontend && npm run lint

up:
	docker compose up --build
