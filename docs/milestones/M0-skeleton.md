# M0 — Skeleton that runs end to end

- Status: Design
- Branch prefix: `m0/`

## 1. Goal and demo

A monorepo where every app builds, lints, typechecks and tests locally and in CI, and the full dev stack
starts with one command.

Demo, from a clean clone:

1. `docker compose up` (or `just dev`) → open `http://localhost:5173` → page shows **API: ok · DB: ok**.
2. `docker compose stop db` → within ~5 s the page shows **DB: error**; the API stays up.
   `docker compose start db` → back to **ok** without a page reload.

## 2. Design

```
browser ──/api/*──▶ Vite dev server (proxy) ──▶ api:8000 (FastAPI, uvicorn --reload) ──▶ db:5432 (Postgres 17)
```

- **Single origin.** The API serves all routes under `/api` itself. The Vite dev proxy (now) and nginx (M7)
  forward `/api/*` unchanged — no path rewriting, no CORS middleware.
- **Python layout.** uv workspace root `pyproject.toml` at the repo root, members `services/*` and `packages/*`.
  The API is a src-layout package:

  ```
  services/api/
    pyproject.toml
    src/obrii_api/
      main.py      # create_app() factory, lifespan
      config.py    # Settings (pydantic-settings), read from env
      db.py        # async engine creation/disposal
      health.py    # router + checks
    tests/
  ```

  Health is platform plumbing, not a domain module, so it sits outside `auth/users/flights/missions/telemetry`.
- **DB access.** SQLAlchemy 2 async engine on asyncpg, created and disposed in the FastAPI `lifespan`.
  No ORM models and no Alembic in M0 (they arrive in M2).
- **Frontend.** Vite + React 19 + TS (strict). TanStack Query polls `/api/health` every 5 s through an
  `openapi-fetch` client typed by `openapi-typescript` output generated from the API's OpenAPI spec.
- **Dev stack.** `compose.yaml` at the repo root (may `include:` files from `infra/`) with `db`, `api`, `web`.
  Source sync via `docker compose watch` (`develop.watch`: sync source, rebuild on lockfile change) — no bind
  mounts over the container's `.venv` / `node_modules`.

## 3. Contracts

### `GET /api/health/live`

Liveness: the process is up and serving. Used by the Docker healthcheck. Never touches dependencies.

```json
200 {"status": "ok"}
```

### `GET /api/health`

Readiness: dependencies are reachable. Used by the UI.

- `200` when every check is `ok`, `503` otherwise. Body has the same shape in both cases.
- DB check: `SELECT 1` bounded by a **1 s timeout**, so a hung Postgres cannot hang the endpoint.

```json
{
  "status": "ok" | "degraded",
  "checks": {
    "db": { "status": "ok" | "error", "latency_ms": 3.1, "detail": null | "<short error message>" }
  }
}
```

Response models are Pydantic; the frontend consumes the generated TS types (both the 200 and 503 responses
are declared in the OpenAPI spec).

### Configuration

| Env var | Example | Used by |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://obrii:obrii@db:5432/obrii` | api |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `obrii` | db |
| `API_PROXY_TARGET` | `http://api:8000` | web (Vite proxy) |

Committed as `.env.example`; `.env` is gitignored.

## 4. Decisions

- **OpenAPI → TS type generation moved from M1 to M0.** The health response is the first API type the frontend
  needs, and types are never hand-written (CLAUDE.md). CI regenerates them and fails on diff.
- **TanStack Query from day one** instead of `fetch` in `useEffect`; polling drives demo step 2.
- **Liveness vs readiness split.** A DB outage must not make Docker restart the API, and the UI needs the
  dependency detail.
- **No `depends_on: service_healthy` from api to db.** The API must start and report a missing DB, not wait for it.
- **`docker compose watch` over bind mounts** for hot reload.
- **`postgres:17` for M0.** PostGIS image choice deferred to M2 (`postgis/postgis` has historically lacked
  arm64 images — check before adopting on Apple Silicon).
- **Unit tests via `app.dependency_overrides`** with fake ok/failing DB checks. Real-Postgres tests start in M2.
- **`packages/contracts` stays empty** until M1 introduces shared message schemas.
- Repo-level choices (monorepo, no Nx, `just`): [ADR 0001](../adr/0001-monorepo-and-modular-monolith.md).

## 5. Tasks

| # | Task | Acceptance check | PR |
|---|------|------------------|----|
| 1 | uv workspace + API skeleton: root `pyproject.toml`, `services/api` package, `create_app()`, `/api/health/live`, ruff/mypy (strict)/pytest config, `justfile` | `just api-check` (ruff check, ruff format --check, mypy, pytest) passes; one test for `/api/health/live` | |
| 2 | Settings + engine lifespan + `/api/health` with DB check and 1 s timeout | Tests cover ok → 200 and failure/timeout → 503 via dependency overrides | |
| 3 | Frontend skeleton: Vite, React 19, TS strict, ESLint (flat config), Prettier, Vitest + Testing Library | `just web-check` (lint, format check, tsc, vitest) passes | |
| 4 | Type generation + health UI: OpenAPI export script, `openapi-typescript`, `openapi-fetch` client, TanStack Query polling, status component | `just gen-types` produces committed types; component test renders ok and error states from mocked responses | |
| 5 | Dev Dockerfiles + root `compose.yaml` (db, api, web) + Vite proxy + `.env.example` + `just dev` | Both demo steps work from a clean clone | |
| 6 | GitHub Actions: path-filtered `api` and `web` jobs, generated-types drift check | CI green on the PR; a stale types file fails it | |
| 7 | Close-out: README quick start, CLAUDE.md Commands section, retro below, tick ROADMAP | Demo re-run from a fresh clone | |

## 6. Open questions

- Should CI also build the Docker images (`docker compose build`)?
- Exact `just` recipe names.
- API Dockerfile base: `ghcr.io/astral-sh/uv` image vs `python:3.14-slim` with the uv binary copied in.

## 7. As built / retro

_Filled at close-out._
