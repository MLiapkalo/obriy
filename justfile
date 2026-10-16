default:
    @just --list

dev:
    docker compose up --build --watch

api-check:
    uv run ruff check services/api packages/contracts
    uv run ruff format --check services/api packages/contracts
    uv run mypy services/api/src services/api/tests packages/contracts/src packages/contracts/tests
    uv run pytest services/api
    uv run pytest packages/contracts

api-fmt:
    uv run ruff check --fix services/api packages/contracts
    uv run ruff format services/api packages/contracts

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

gen-types:
    uv run python -m obriy_api.openapi > services/api/openapi.json
    pnpm dlx --package=openapi-typescript@7.13.0 --package=typescript@5.9.3 openapi-typescript services/api/openapi.json -o frontend/src/api/schema.d.ts
