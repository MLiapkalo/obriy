# Obrii

*Обрій — "horizon" in Ukrainian.*

A browser-based ground control station (GCS) for unmanned aerial vehicles: live telemetry on a map,
mission planning, vehicle commands, flight recording and replay, live video — designed to run fully offline.

> Status: early development — see [ROADMAP.md](ROADMAP.md).

## Architecture

- `frontend/` — React + TypeScript (Vite), MapLibre GL.
- `services/api/` — FastAPI modular monolith: auth, users, flights, missions, telemetry fan-out.
- `services/gateway/` — vehicle link service (MAVLink over UDP), introduced in M5.
- `packages/contracts/` — shared Pydantic message schemas used by the Python services.
- `infra/` — Docker Compose, ArduPilot SITL, MediaMTX configuration.
- `docs/adr/` — architecture decision records. `docs/milestones/` — per-milestone design docs.

## Quick start

_Coming in M0._
