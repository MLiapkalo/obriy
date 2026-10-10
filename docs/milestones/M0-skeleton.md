# M0 — Skeleton that runs end to end

- Status: Done
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
browser ──/api/*──▶ Vite dev server (proxy) ──▶ api:8000 (FastAPI, uvicorn --reload) ──▶ db:5432 (Postgres 18)
```

- **Single origin.** The API serves all routes under `/api` itself. The Vite dev proxy (now) and nginx (M7)
  forward `/api/*` unchanged — no path rewriting, no CORS middleware.
- **Python layout.** uv workspace root `pyproject.toml` at the repo root (virtual: no `[project]`; holds the
  workspace members, the shared dev dependency group and ruff/mypy config). Members are `services/*`;
  `packages/*` is added in M1 when `packages/contracts` gets its own `pyproject.toml` (uv rejects a member
  directory without one). The API is a src-layout package:

  ```
  services/api/
    pyproject.toml
    src/obriy_api/
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
    "db": { "status": "ok" | "error", "latency_ms": 3.1, "detail": null | "<root-cause exception type, e.g. InvalidPasswordError>" }
  }
}
```

Response models are Pydantic; the frontend consumes the generated TS types (both the 200 and 503 responses
are declared in the OpenAPI spec).

### Configuration

| Env var | Example | Used by |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://obriy:root@db:5432/obriy` | api |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `obriy` / `root` / `obriy` | db |
| `API_PROXY_TARGET` | `http://api:8000` | web (Vite proxy) |

`compose.yaml` holds dev defaults for `POSTGRES_*` (`${VAR:-default}`), builds `DATABASE_URL` from them and
sets `API_PROXY_TARGET`, so a clean clone needs no `.env`. Overrides go in a root `.env` (gitignored);
`.env.example` documents them.

## 4. Decisions

- **OpenAPI → TS type generation moved from M1 to M0.** The health response is the first API type the frontend
  needs, and types are never hand-written (CLAUDE.md). CI regenerates them and fails on diff.
- **TanStack Query from day one** instead of `fetch` in `useEffect`; polling drives demo step 2.
- **Liveness vs readiness split.** A DB outage must not make Docker restart the API, and the UI needs the
  dependency detail.
- **No `depends_on: service_healthy` from api to db.** The API must start and report a missing DB, not wait for it.
- **`docker compose watch` over bind mounts** for hot reload.
- **`postgres:18.6`** (design said 17; no reason to start a new project a major behind). 18+ images keep data in
  a versioned subdirectory, so the volume is mounted at `/var/lib/postgresql`, not `…/data`. PostGIS image
  choice deferred to M2 (`postgis/postgis` has historically lacked arm64 images — check before adopting on
  Apple Silicon).
- **API image: `python:3.14-slim` + pinned uv binary** (`COPY --from=ghcr.io/astral-sh/uv`), so Python and uv
  upgrade independently. The uv version is set once in the root `pyproject.toml`
  (`[tool.uv] required-version`, also read by setup-uv in CI); the Dockerfile tag must match it.
  Dependencies are installed in their own layer (`--no-install-workspace`) before the
  source is copied; the workspace member is an editable install, so synced source is picked up by `--reload`.
- **Web image: `ghcr.io/pnpm/pnpm`, Node pinned via `devEngines.runtime`** in `package.json` (replaces the
  `packageManager` field). pnpm downloads the exact Node version during install, so the host and the image
  run the same Node. CI's `pnpm/setup` reads both versions from `devEngines` too.
- **`init: true` for `web`.** As PID 1, Vite ignores SIGINT; an init process forwards signals so Ctrl+C and
  `docker compose stop` work. uvicorn handles signals itself.
- **Unit tests via `app.dependency_overrides`** with fake ok/failing DB checks. Real-Postgres tests start in M2.
- **oxlint instead of ESLint.** `typescript-eslint` only supports TypeScript < 6.1, so type-aware ESLint rules
  would pin the frontend to TS 6. oxlint's type-aware mode (`oxlint-tsgolint`) runs on tsgo (TS 7) and has the
  typescript, react/react-hooks, jsx-a11y and import rules built in.
- **`openapi-typescript` runs via `pnpm dlx` with TypeScript 5.9.** It uses the TS compiler JS API that TS 7
  no longer exposes (peer range `typescript ^5`), and pnpm resolves peers from the project, so it can't be a
  regular dev dependency. Versions are pinned in the `gen-types` recipe; move it back to `devDependencies` once
  it supports TS 7. The exported spec is committed at `services/api/openapi.json` next to the generated types.
- **CI: one workflow per concern** (`api`, `web`, `types`), each with its own `paths:` filter, since `paths`
  applies per workflow, not per job. The types drift check is separate because it must run on changes to
  either the API or `frontend/src/api/`. Third-party actions are pinned by commit SHA.
- **CI does not build Docker images** in M0. `just dev` exercises them locally; revisit when images are
  deployed or published.
- **`packages/contracts` stays empty** until M1 introduces shared message schemas.
- Repo-level choices (monorepo, no Nx, `just`): [ADR 0001](../adr/0001-monorepo-and-modular-monolith.md).

## 5. Tasks

| # | Task | Acceptance check | PR |
|---|------|------------------|----|
| 1 | uv workspace + API skeleton: root `pyproject.toml`, `services/api` package, `create_app()`, `/api/health/live`, ruff/mypy (strict)/pytest config, `justfile` | `just api-check` (ruff check, ruff format --check, mypy, pytest) passes; one test for `/api/health/live` | ✅ [#1](https://github.com/MLiapkalo/obriy/pull/1) |
| 2 | Settings + engine lifespan + `/api/health` with DB check and 1 s timeout | Tests cover ok → 200 and failure/timeout → 503 via dependency overrides | ✅ [#2](https://github.com/MLiapkalo/obriy/pull/2) |
| 3 | Frontend skeleton: Vite, React 19, TS 7 strict, oxlint (type-aware), Prettier, Vitest + Testing Library | `just web-check` (lint, format check, tsc, vitest) passes | ✅ [#3](https://github.com/MLiapkalo/obriy/pull/3) |
| 4 | Type generation + health UI: OpenAPI export script, `openapi-typescript`, `openapi-fetch` client, TanStack Query polling, status component | `just gen-types` produces committed types; component test renders ok and error states from mocked responses | ✅ [#4](https://github.com/MLiapkalo/obriy/pull/4) |
| 5 | Dev Dockerfiles + root `compose.yaml` (db, api, web) + Vite proxy + `.env.example` + `just dev` | Both demo steps work from a clean clone | ✅ [#5](https://github.com/MLiapkalo/obriy/pull/5) |
| 6 | GitHub Actions: path-filtered `api`, `web` and `types` (generated-types drift check) workflows | CI green on the PR; a stale types file fails it | ✅ [#6](https://github.com/MLiapkalo/obriy/pull/6) |
| 7 | Close-out: README quick start, CLAUDE.md Commands section, retro below, tick ROADMAP | Demo re-run from a fresh clone | ✅ [#7](https://github.com/MLiapkalo/obriy/pull/7) |

## 6. Open questions

_None._

## 7. As built / retro

Built 2026-10-07 → 2026-10-10 in six PRs (#1–#6); demo passed from a fresh clone.

**Deviations from the design** (details in §4):
- OpenAPI → TS type generation pulled forward from M1.
- Postgres 18 instead of 17; volume mounted at `/var/lib/postgresql`.
- oxlint instead of ESLint, to stay on TypeScript 7; `openapi-typescript` runs via `pnpm dlx` on TS 5.9.
- Health `detail` reports the root-cause exception type (follows `__cause__`), not the SQLAlchemy wrapper.
- CI is three path-filtered workflows (`api`, `web`, `types`) rather than two jobs; no Docker builds in CI.
- Tool versions have one source each: uv via `required-version`, pnpm and Node via `devEngines`, read by
  both local tooling and CI.

**What went well:**
- Contract-first health endpoint: the generated types made the frontend side mechanical, and the drift check
  keeps them honest.
- Liveness/readiness split held up in the demo: stopping the DB degrades the UI without restarting the API.

**What to change:** nothing significant. Adopting current major versions (TS 7, pnpm 12, Postgres 18) was
deliberate; the workarounds it needed are recorded in §4.
