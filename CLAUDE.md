# CLAUDE.md

Project context for Claude Code sessions in this repo.

## Project

Obriy — web ground control station for drones. Plan and progress: `ROADMAP.md`.
Current milestone design doc: `docs/milestones/`. Lasting decisions: `docs/adr/`.

## Working agreement

- The owner writes the feature code. Claude helps with system design and architecture decisions, explains,
  unblocks, reviews diffs and suggests improvements. Claude writes code only when explicitly asked
  (boilerplate/config is fine on request).
- Workflow per milestone: design session → `docs/milestones/Mx-*.md` (contracts + tasks) → one branch/PR per task →
  review → close-out (fill "As built / retro", tick ROADMAP).
- When implementation deviates from the design doc, update the doc in the same PR.
- In reviews, prioritise: correctness, idiomatic Python/React, design boundaries, tests — then style.

## Documentation maintenance

Keep docs in sync with reality without being asked. Update them in the same change that makes them stale,
and mention the doc updates in your reply.

Where status lives:
- `ROADMAP.md` → "Progress" checklist: milestone state (`[ ]` todo, `[~]` in progress, `[x]` done) plus a one-line
  current focus under it (milestone, task, what's next).
- `docs/milestones/Mx-*.md` → `Status` field and the Tasks table (task state + PR link).

When to update:
- **Design session ends** → milestone doc is complete (contracts, tasks), status `Design` → `In progress`;
  ROADMAP milestone `[~]`, current focus updated.
- **Task merged / finished** → task row marked done with PR link; current focus moves to the next task.
- **Implementation deviates from the design** (contract, schema, endpoint, message shape, component split) →
  update the milestone doc's Contracts/Design sections.
- **A lasting decision is made or reversed** → new ADR, or mark the old one `Superseded by NNNN`.
- **Commands, setup, tooling, env vars or ports change** → update `README.md` (quick start) and the Tooling
  section of this file.
- **Repo layout or architecture rules change** → update this file and the README architecture section.
- **Milestone demo passes** → fill "As built / retro" (draft it, owner confirms), status `Done`, ROADMAP `[x]`.

Rules:
- Docs describe what exists, not plans dressed up as facts; plans stay in ROADMAP and milestone docs.
- Small, factual edits; don't rewrite sections that are still accurate.
- If unsure whether something is a deviation worth recording, ask.

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
