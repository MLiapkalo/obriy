# CLAUDE.md

Project context for Claude Code sessions in this repo.

## Project

Obrii — web ground control station for drones. Plan and progress: `ROADMAP.md`.
Current milestone design doc: `docs/milestones/`. Lasting decisions: `docs/adr/`.

## Working agreement

- The owner writes the feature code. Claude helps with system design and architecture decisions, explains,
  unblocks, reviews diffs and suggests improvements. Claude writes code only when explicitly asked
  (boilerplate/config is fine on request).
- Workflow per milestone: design session → `docs/milestones/Mx-*.md` (contracts + tasks) → one branch/PR per task →
  review → close-out (fill "As built / retro", tick ROADMAP).
- When implementation deviates from the design doc, update the doc in the same PR.
- In reviews, prioritise: correctness, idiomatic Python/React, design boundaries, tests — then style.

## Architecture rules

- Monorepo, modular monolith API. Separate services only with a deployment/failure-isolation reason (see ADR 0001).
- API modules (`auth`, `users`, `flights`, `missions`, `telemetry`) talk to each other only through each module's
  public interface, never by importing another module's internals or tables.
- Vehicle access goes through the `VehicleLink` interface; fake and MAVLink are implementations.
- Shared message schemas live in `packages/contracts`. Frontend TS types are generated from the API's OpenAPI spec,
  never hand-written.
- No runtime dependency on the internet (tiles, fonts, assets are self-hosted).

## Tooling

- Python 3.14, `uv` workspace, `ruff` (lint + format), `mypy --strict`, `pytest`.
- Frontend: Node 22+, `pnpm`, Vite, ESLint, Prettier, Vitest.
- `just` as the task runner; Docker Compose for local stack.
- Commands: _to be filled in during M0._
