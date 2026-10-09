default:
    @just --list

api-check:
    uv run ruff check services/api
    uv run ruff format --check services/api
    uv run mypy services/api/src services/api/tests
    uv run pytest services/api

api-fmt:
    uv run ruff check --fix services/api
    uv run ruff format services/api

api-run:
    uv run uvicorn --factory obriy_api.main:create_app --reload

web-check:
    pnpm --dir frontend lint
    pnpm --dir frontend format:check
    pnpm --dir frontend typecheck
    pnpm --dir frontend test

web-fmt:
    pnpm --dir frontend lint:fix
    pnpm --dir frontend format

web-dev:
    pnpm --dir frontend dev
