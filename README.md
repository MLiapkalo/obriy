# Obriy

*Обрій — "horizon" in Ukrainian.*

A browser-based ground control station (GCS) for unmanned aerial vehicles: live telemetry on a map,
mission planning, vehicle commands, flight recording and replay, live video — designed to run fully offline.

> Status: early development — see [ROADMAP.md](ROADMAP.md).

## Architecture

- `frontend/` — React + TypeScript (Vite). API types are generated from the API's OpenAPI spec.
- `services/api/` — FastAPI modular monolith on Postgres (async SQLAlchemy). Currently health endpoints only;
  domain modules arrive with later milestones.
- `packages/contracts/` — shared message schemas (Pydantic), a uv workspace member used by the API; injected
  into its OpenAPI spec, so the frontend gets their TS types.
- `infra/` — placeholder for infrastructure config (SITL, MediaMTX).
- `compose.yaml` — local dev stack: Postgres, API, web.
- `docs/adr/` — architecture decision records. `docs/milestones/` — per-milestone design docs.

Planned components (vehicle gateway, map, video) are described in [ROADMAP.md](ROADMAP.md).

## Quick start

Requires Docker with Compose v2.

```sh
just dev    # docker compose up --build --watch
```

Open http://localhost:5173. The API is on http://localhost:8000 (`/docs` for OpenAPI).
Defaults need no configuration; to override database credentials, copy `.env.example` to `.env`.

## Development

Running checks on the host needs [uv](https://docs.astral.sh/uv/), [pnpm](https://pnpm.io/) and
[just](https://just.systems/). Exact versions are pinned in the repo: uv via `required-version` in
`pyproject.toml`, pnpm and Node via `devEngines` in `frontend/package.json`.

| Command | What it does |
|---|---|
| `just dev` | Full stack in Docker with hot reload (`docker compose up --build --watch`) |
| `just api-check` | ruff lint + format check, mypy (strict), pytest |
| `just api-fmt` | ruff autofix + format |
| `just api-run` | API on the host with reload; needs `DATABASE_URL` |
| `just web-check` | oxlint, Prettier check, tsc, Vitest |
| `just web-fmt` | oxlint autofix + Prettier |
| `just web-dev` | Vite dev server on the host |
| `just gen-types` | Export the OpenAPI spec and regenerate frontend types; commit both |

CI (GitHub Actions) runs `api-check`, `web-check` and a generated-types drift check on pull requests,
each filtered to the paths it depends on.
