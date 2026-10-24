# Web Ground Control Station — Roadmap

A browser-based ground control station (GCS) for a drone: live telemetry on a map, mission planning,
commands, flight history, video, offline-ready. Built incrementally — **every milestone ends with a
working system you can demo with `docker compose up`.**

---

## How we work

1. **Design** — we discuss the milestone's architecture and decisions before code. Decisions go in `docs/adr/`.
2. **Break down** — the milestone becomes 4–8 small tasks (one branch/PR each).
3. **Implement** — one branch/PR per task.
4. **Review** — every diff is reviewed for correctness, idioms, design boundaries and tests.
5. **Demo + retro** — milestone is done when its demo works from a clean `docker compose up`. Record deviations
   from the design.

Rule of thumb: if a task takes more than ~2 evenings, it's too big — split it.

---

## Target architecture (end state)

```
                    ┌──────────────────────────────────────────┐
  Browser           │  React + TS (Vite)                        │
                    │  MapLibre map · HUD · mission planner     │
                    │  video panel · flight history             │
                    └──────┬───────────────┬──────────┬─────────┘
                     REST  │        WebSocket│   WebRTC│
                    ┌──────▼───────────────▼──┐  ┌────▼─────────┐
                    │  API service (FastAPI)   │  │  MediaMTX    │
                    │  auth · missions ·       │  │  (video      │
                    │  flights · WS fan-out    │  │   relay)     │
                    └──────┬──────────┬────────┘  └────▲─────────┘
                           │          │ pub/sub         │ RTSP
                    ┌──────▼─────┐ ┌──▼──────┐         │
                    │ Postgres + │ │ Redis   │         │
                    │ PostGIS    │ │ (bus)   │         │
                    └────────────┘ └──▲──────┘         │
                                      │                 │
                    ┌─────────────────┴──────┐  ┌──────┴───────┐
                    │ Vehicle gateway (Python)│  │ Camera sim   │
                    │ pymavlink · adapters    │  │ (ffmpeg)     │
                    └─────────────┬───────────┘  └──────────────┘
                                  │ MAVLink / UDP
                    ┌─────────────▼───────────┐
                    │ ArduPilot SITL (Docker) │  ← or the built-in fake simulator
                    └─────────────────────────┘
```

Key ideas:
- **REST for resources** (flights, missions, users), **WebSocket for real-time** (telemetry down, commands up).
- **Ports & adapters** for the vehicle link: the system talks to a `VehicleLink` interface; the fake simulator
  and real MAVLink are two implementations. This lets us start without any drone tooling.
- **One source of truth for types**: Pydantic models → OpenAPI → generated TS types (`openapi-typescript`).
- **Offline first**: no runtime dependency on the internet (tiles, fonts, images all self-hosted).

---

## Stack decisions

| Area | Choice | Why |
|---|---|---|
| Frontend | React 19 + TS + Vite | Component model and ecosystem suit a real-time SPA. Vite instead of Next.js: a GCS is a SPA, no SSR needed |
| State / data | TanStack Query (server state) + Zustand (client/live state) | Industry default; clean split between REST cache and live telemetry |
| Map | MapLibre GL JS | Open source, WebGL rendering, offline vector tiles |
| Backend | Python 3.14 + FastAPI | Async, typed, built-in dependency injection and OpenAPI generation; drone tooling (pymavlink, ArduPilot) is Python |
| Python tooling | `uv` (packages, venvs, Python versions), `ruff` (lint + format), `mypy` strict (static types), `pytest` | Modern and fast; strict typing catches errors early in a dynamically typed language |
| ORM / migrations | SQLAlchemy 2 (async) + Alembic | De facto standard ORM and migration tool in Python |
| DB | Postgres 18 + PostGIS | Spatial types and queries for tracks and missions |
| Bus | Redis pub/sub (decided at M5) | Simple; NATS considered as alternative |
| Drone sim | ArduPilot SITL in Docker | Real autopilot, speaks real MAVLink, works with QGroundControl |
| Video | ffmpeg → MediaMTX → WebRTC (WHEP) | Low latency in browser, no custom media server code |
| Infra | Docker Compose, GitHub Actions | Reproducible local stack and CI; the same images run offline in the field |
| Repo | Monorepo: `frontend/`, `services/api/`, `services/gateway/`, `packages/contracts/`, `infra/`, `docs/` | One PR can change schema + API + UI together; see ADR 0001 |

---

## Milestones

Estimates are rough and revisited after each milestone.

### M0 — Skeleton that runs end to end (≈1 week)

**Demo:** `docker compose up` → browser shows "API: ok, DB: ok", read from the backend; stop the db → UI shows "DB: error".

Design doc: [docs/milestones/M0-skeleton.md](docs/milestones/M0-skeleton.md).

Scope:
- Monorepo layout, README, `.editorconfig`, `.gitignore`.
- `services/api/`: FastAPI app in a `uv` workspace, `/health` endpoint checking DB connection, `ruff` + `mypy` + `pytest` with one test.
- `frontend/`: Vite React TS app, polls `/api/health` (TanStack Query), oxlint + Prettier + Vitest.
- OpenAPI → TS type generation script (moved here from M1) + CI drift check.
- Root `compose.yaml`: postgres, backend, frontend (dev mode with hot reload via `docker compose watch`).
- GitHub Actions: lint + typecheck + test for both apps.
- `docs/adr/0001-monorepo-and-stack.md`.

---

### M1 — A fake drone flying on a map (≈2 weeks)

**Demo:** open the page → a drone icon moves along a circle on the map; HUD shows altitude, speed,
heading, battery, updating 10×/sec. Kill the backend → UI shows "link lost", reconnects when it's back.

Design doc: [docs/milestones/M1-fake-drone.md](docs/milestones/M1-fake-drone.md).

Scope:
- `VehicleLink` interface (a `typing.Protocol`, i.e. structural typing) + `FakeVehicle` implementation (async loop generating telemetry). Lives inside the API for now; moves to `services/gateway/` in M5.
- Pydantic `Telemetry` model; WebSocket endpoint `/api/ws/telemetry` broadcasting to all clients.
- Frontend: MapLibre map, drone marker with heading, HUD panel, `useTelemetry` hook with
  reconnect + exponential backoff, connection status indicator.
- Tests: simulator unit test, WebSocket test with FastAPI `TestClient`.

Design talk before coding: message envelope format (`{type, ts, payload}`), update rates, backpressure.

---

### M2 — Flights are recorded and replayable (≈2 weeks)

**Demo:** start a flight, fly, stop → it appears in "Flight history"; open it → full track drawn on the map,
with a timeline slider to replay position and telemetry.

Scope:
- PostGIS; SQLAlchemy models `Flight`, `TelemetrySample` (geometry point); Alembic migrations.
- Batched writes (buffer samples, flush every N ms) — don't do one INSERT per message.
- REST: `POST /flights`, `POST /flights/{id}/stop`, `GET /flights`, `GET /flights/{id}/track` (GeoJSON).
- Frontend: routing (React Router), flights list with TanStack Query, track layer, replay slider.
- Tests with a real Postgres in Docker (pytest fixtures and their scopes).

---

### M3 — Users, auth and roles (≈1.5 weeks)

**Demo:** log in as `viewer` → you see telemetry but command buttons are disabled and the API rejects
commands with 403. Log in as `operator` → commands allowed. `admin` manages users.

Scope:
- Users table, password hashing (argon2), JWT access token + refresh token in httpOnly cookie.
- Role-based dependency guards for REST **and** WebSocket (auth on WS handshake).
- Frontend: login page, auth context, protected routes, role-aware UI.
- Seed script for dev users. Security tests (expired token, wrong role, no token on WS).

---

### M4 — Missions and commands (≈2.5 weeks)

**Demo:** operator clicks waypoints on the map, sets altitudes, saves the mission, presses
"Upload & Start" → the fake drone takes off, flies the waypoints, returns home. "RTL" and "Pause"
work mid-flight. Each command shows pending → acknowledged / failed / timed out.

Scope:
- `Mission` model (waypoints as PostGIS LineString + per-point params), CRUD API.
- Command channel over WS: client sends `{cmd_id, type, args}`, server replies with ack/result;
  timeouts and a per-vehicle command queue.
- Vehicle state machine (`DISARMED → ARMED → TAKEOFF → MISSION → RTL → LANDED`) in `FakeVehicle`.
- Frontend: mission editor (add/drag/delete waypoints), mission list, command panel with status.
- Tests for the state machine and command timeouts.

---

### M5 — Real autopilot via MAVLink (≈2.5 weeks)

**Demo:** same UI, same buttons — but now it's a real ArduPilot (SITL) flying. You can open
QGroundControl at the same time and see the same drone.

Scope:
- ArduPilot SITL container in compose.
- New `services/gateway/` service (FakeVehicle moves here too): `MavlinkVehicle` implementing `VehicleLink` with `pymavlink` over UDP;
  maps MAVLink messages (HEARTBEAT, GLOBAL_POSITION_INT, ATTITUDE, SYS_STATUS…) to our `Telemetry`;
  mission upload protocol; commands (`COMMAND_LONG` arm/takeoff/RTL).
- Redis pub/sub between gateway and API (telemetry topic, command topic). ADR: Redis vs NATS.
- Config switch: `VEHICLE=fake|sitl`.
- Link health: heartbeat timeout → "link lost" end to end.

---

### M6 — Live video (≈1.5 weeks)

**Demo:** video panel next to the map shows a live "camera" stream with < 500 ms latency; panel
handles stream loss and reconnects.

Scope:
- Camera simulator: ffmpeg test pattern (with timestamp overlay) → RTSP → MediaMTX.
- Browser playback via WebRTC (WHEP); HLS fallback.
- Latency measurement overlay; resizable map/video layout.

---

### M7 — Field-ready: offline, resilient, observable (≈2 weeks)

**Demo:** disconnect from the internet, `docker compose up` → everything works, including map tiles.
Restart the gateway mid-flight → UI shows degraded state and recovers without page reload.

Scope:
- Self-hosted offline tiles (PMTiles for Ukraine region) + self-hosted map fonts/sprites.
- Production compose profile: built frontend served by nginx, no dev servers, healthchecks, restart policies.
- Images can be exported/imported for air-gapped machines (`docker save`/`load` script).
- Structured JSON logging, request IDs, basic Prometheus metrics (+ optional Grafana).
- E2E tests with Playwright for the core flows (login → plan → fly).

---

### M8 — Stretch goals (optional, 1–2 weeks each)

- **Multi-vehicle** — fleet view, select vehicle, per-vehicle command queues.
- **Gamepad manual control** — Gamepad API → low-latency control messages.
- **Desktop packaging** — wrap the frontend in Electron with IPC to a local gateway.
- **Node.js service** — rewrite the gateway (or a new service) in TS with `node-mavlink` to compare.
- **3D terrain** — Three.js / deck.gl terrain view.

---

## Progress

**Current focus:** M1 — Fake drone on a map; tasks 1–3 done, next: task 4 (WS endpoint `/api/ws/telemetry` + Vite proxy `ws: true`).

- [x] M0 — Skeleton
- [~] M1 — Fake drone on a map
- [ ] M2 — Flight recording & replay
- [ ] M3 — Auth & roles
- [ ] M4 — Missions & commands
- [ ] M5 — Real MAVLink (SITL)
- [ ] M6 — Live video
- [ ] M7 — Field-ready
- [ ] M8 — Stretch
