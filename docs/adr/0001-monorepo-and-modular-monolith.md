# ADR 0001 — Monorepo and modular monolith

- Status: Accepted
- Date: 2026-10-07

## Context

Obriy is built by one developer, in milestones, as both a working system and a public portfolio piece.
It spans a React frontend, Python backend services, shared message schemas, and infrastructure
(Postgres, autopilot simulator, media server). Changes frequently cross the API/UI boundary.

## Decision

1. **Single repository** containing frontend, services, shared packages, infra and docs.
2. **Modular monolith** for the API: one FastAPI service with strictly bounded internal modules
   (`auth`, `users`, `flights`, `missions`, `telemetry`). Modules interact only through public interfaces.
3. **Separate services only where a deployment or failure-isolation boundary exists:**
   - Vehicle gateway (from M5): talks MAVLink/UDP to the vehicle, must survive API restarts, and in field
     deployments runs close to the radio link, possibly on a different machine than the API.
   - Media server (MediaMTX, off-the-shelf).
4. **No Nx/Turborepo.** The repo is polyglot (one TS app, several Python packages). `uv` workspaces manage
   Python packages, `pnpm` manages the frontend, `just` provides a single command entry point, and CI uses
   path filters instead of a dependency graph. Revisit if multiple JS/TS packages appear.

## Consequences

- One PR can change schema, API and UI atomically; one CI setup; one README and demo for reviewers.
- Shared schemas in `packages/contracts` can't drift between services.
- One deployable API keeps transactions and debugging simple; module boundaries keep later extraction cheap.
- Discipline needed: module boundaries are enforced by convention and review, not by process isolation.
- CI runs more than strictly necessary on some changes; acceptable at this size.
