# M1 — A fake drone flying on a map

- Status: In progress
- Branch prefix: `m1/`

## 1. Goal and demo

A simulated drone streams live telemetry from the API to the browser over a WebSocket; the UI shows it on a map
and in a HUD, and survives the backend going away.

Demo, from a clean clone:

1. `just dev` → open `http://localhost:5173` → a drone icon flies a 200 m circle around home (Kyiv by default),
   leaving a trail; the HUD shows altitude, speed, heading and battery, updating 10×/s; status shows **Link OK**.
2. Open a second tab → both tabs show the drone at the same position.
3. `docker compose stop api` → within ~1 s both tabs show **Link lost**, last known values greyed out.
   `docker compose start api` → both tabs reconnect within ~10 s, without a page reload.

## 2. Design

```
FakeVehicle ──▶ reader task ──▶ TelemetryBroadcaster ─┬─▶ queue ──▶ WS handler ──▶ tab A
(VehicleLink)   (lifespan,       (serializes once,     ├─▶ queue ──▶ WS handler ──▶ tab B
                 one per app)     queue per client)    └─▶ …
                                                                      │
                          browser: TelemetryClient ──▶ Zustand store ─┼─▶ HUD, status (selectors)
                                                                      └─▶ map marker + trail (store.subscribe)
```

**Telemetry** is a stream of state snapshots: each sample fully replaces the previous one. The UI only needs the
newest sample; history is M2. Rate: 10 Hz.

### Backend

- **`VehicleLink`** (`typing.Protocol`): the only way the rest of the API sees a vehicle. M1 needs only
  a telemetry stream; commands arrive in M4. Implementations: `FakeVehicle` (M1), `MavlinkVehicle` (M5), scripted
  test vehicles. Lives in `obriy_api/vehicle/`; moves to `services/gateway/` in M5.
- **`FakeVehicle`**: a pure `state_at(t)` (t = seconds since start) computes the state, so tests need no sleeping
  and errors don't accumulate; `telemetry()` is an async generator that yields `state_at(monotonic elapsed)` and
  then `await asyncio.sleep(1 / rate_hz)`. Elapsed time is read from `time.monotonic()`, not counted in ticks.
  Flight model (home = circle centre, `r` = 200 m, `v` = 10 m/s, compass angle θ: 0 = north, clockwise):

  | Quantity | Formula |
  |---|---|
  | angle (rad) | `θ = v·t / r` (one lap ≈ 126 s) |
  | offset north / east (m) | `r·cos θ`, `r·sin θ` |
  | lat | `home_lat + north / 111320` |
  | lon | `home_lon + east / (111320 · cos(radians(home_lat)))` |
  | heading (deg) | `(degrees(θ) + 90) % 360` |
  | altitude / groundspeed | constant 50 m / 10 m/s |
  | battery % | `100 − 80 · (t % 300) / 300` (100 → 20 % over 5 min, then restarts) |
  | battery V | `14.0 + 2.8 · pct / 100` |

- **Reader task**: started with `asyncio.create_task` in `lifespan`, kept on `app.state`, cancelled and awaited on
  shutdown. Reads `vehicle.telemetry()`, wraps each sample in a `TelemetryMessage` with `ts` = now, serializes it
  once and publishes it. On an exception: log, wait 1 s, restart the stream.
- **`TelemetryBroadcaster`** (`obriy_api/telemetry/`): holds one `asyncio.Queue(maxsize=10)` per connected client.
  `publish` puts the JSON string into every queue without awaiting; when a queue is full it drops the oldest item
  first. A slow client gets fewer, never older, samples and never slows the producer or other clients.
- **WS handler** (`/api/ws/telemetry`): accept → subscribe → `asyncio.TaskGroup` with a send loop
  (queue → `send_text`) and a receive loop (`receive_text`, ignores input in M1, raises on disconnect); when either
  ends the group cancels the other → unsubscribe in `finally`. Dead peers are closed by uvicorn's ping (20 s).

### Frontend

- **`TelemetryClient`** (plain TS class, `src/telemetry/`): owns the WebSocket, reconnect backoff and staleness
  timer; writes into a Zustand store. Testable without React.
- **`useTelemetryConnection()`**: called once in `App`; its effect calls `client.start()` / `client.stop()`.
- **Status**: `connecting` (opening) · `live` (open, messages arriving) · `stale` (open, no message > 1 s) ·
  `lost` (closed, retry scheduled). After 5 s of silence the client closes the socket and reconnects (catches
  half-open connections). Staleness uses the browser's receive time, never `ts` (clock skew).
- **Backoff**: wait = `min(10 s, 0.5 s · 2^attempt) · Math.random()` (full jitter); attempt resets on `open`.
- **Rendering**: HUD and status read the store through selectors and re-render only when their value changes.
  The map component renders once; an effect uses `store.subscribe` to move the marker (`setLngLat([lon, lat])`,
  rotation = heading) and update the trail source. While the link is lost, last known values stay visible, greyed.
- **Map**: `maplibre-gl` used directly (bundled from npm, no CDN). Layers: drone icon rotated by heading, trail
  (last 30 s = 300 positions), home marker. Starts centred on home at zoom ~16, no auto-follow. Basemap: plain
  background by default; if `VITE_BASEMAP_URL` is set, a raster tile layer from that URL template plus an
  attribution line.

## 3. Contracts

### Telemetry message (`packages/contracts` → `obriy_contracts`)

```json
{
  "type": "telemetry",
  "ts": 1791712800123,
  "payload": {
    "vehicle_id": "fake-1",
    "lat": 50.451577,
    "lon": 30.521353,
    "alt_rel_m": 50.0,
    "groundspeed_mps": 10.0,
    "heading_deg": 118.6,
    "battery_voltage_v": 16.72,
    "battery_remaining_pct": 97
  }
}
```

`TelemetryMessage`:

| Field | Type | Meaning |
|---|---|---|
| `type` | `Literal["telemetry"]` | message kind; one class per kind, union added when a second kind exists (M4) |
| `ts` | int, ≥ 0 | epoch milliseconds (UTC), set by the API when the sample arrives from the vehicle |
| `payload` | `Telemetry` | |

`Telemetry`:

| Field | Type | Meaning |
|---|---|---|
| `vehicle_id` | str | which vehicle |
| `lat` | float, −90..90 | degrees |
| `lon` | float, −180..180 | degrees |
| `alt_rel_m` | float | metres above home |
| `groundspeed_mps` | float, ≥ 0 | metres/second over ground |
| `heading_deg` | float, 0 ≤ x < 360 | nose direction, clockwise from north |
| `battery_voltage_v` | float, ≥ 0 | measured volts |
| `battery_remaining_pct` | int 0..100 \| null | estimate; null when unknown |

Units are part of field names. Messages are JSON text frames. Both models reject unknown keys
(`extra="forbid"`). The models are added to the OpenAPI spec's `components.schemas` (FastAPI does not describe
WebSockets) by an `ObriyAPI(FastAPI)` subclass overriding `openapi()`, using the serialization-mode schema with
defaults required (so `type` is non-optional in TS); `just gen-types` emits their TS types and the CI drift check
covers them.

### `WS /api/ws/telemetry`

- Server → client: one `TelemetryMessage` per sample, ~10/s. A slow client may miss samples (drop-oldest).
- Client → server: nothing in M1 (ignored).
- Vite dev proxy forwards `/api` with `ws: true`.

### `VehicleLink`

```python
class VehicleLink(Protocol):
    def telemetry(self) -> AsyncIterator[Telemetry]: ...
```

Plain `def`: calling an async generator function returns the iterator without `await`.

### `TelemetryBroadcaster`

- `subscribe() -> asyncio.Queue[str]`, `unsubscribe(queue)`, `publish(message_json: str) -> None`.
- Queue size 10; full queue → drop oldest, then put.

### Configuration

| Env var | Default | Used by |
|---|---|---|
| `FAKE_HOME_LAT` / `FAKE_HOME_LON` | `50.45` / `30.52` (Kyiv) | api |
| `VITE_BASEMAP_URL` | empty (plain background) | web |

## 4. Decisions

- **WebSocket, not polling or SSE.** 10 Hz polling costs a request per sample and adds up to one interval of delay;
  SSE is server → client only, and M4 sends commands up the same connection.
- **`/api/ws/telemetry`** instead of the roadmap's `/ws/telemetry`: keeps M0's single `/api` prefix for proxies.
- **One reader + broadcaster** instead of each handler reading the vehicle: one vehicle stream shared by all tabs
  (each handler reading its own would start a separate fake drone; a real radio link can't be opened per tab).
- **Per-client bounded queue, drop oldest.** Telemetry is state: the newest sample makes older ones worthless.
  Unbounded queues grow memory and delay; slowing the producer couples clients. Telemetry-only policy — M4 events
  (command acks) must not be dropped.
- **`TaskGroup` per connection**: send and receive loops can't outlive the handler and errors aren't lost.
- **Envelope `{type, ts, payload}`** with concrete classes per type (no generic `Envelope[T]`, which produces
  awkward schema names); `Telemetry` stays free of transport fields so M2 can store it as is.
- **`ts` as integer epoch ms**: unambiguous UTC, native to JS `Date`, cheaper than ISO strings.
- **JSON text frames**: ~3 KB/s per client; readability in devtools matters more than size.
- **Contract models injected into OpenAPI** rather than a second codegen pipeline: one source of TS types, one
  drift check.
- **`TelemetryClient` class + Zustand** instead of the roadmap's "`useTelemetry` hook with reconnect": one
  connection per app, tests without React, no StrictMode double-connect. TanStack Query stays for REST.
- **Map updates bypass React rendering** (`store.subscribe` → MapLibre calls); only HUD/status re-render.
- **Basemap: plain by default, optional online raster via `VITE_BASEMAP_URL`.** Keeps the no-internet rule by
  default; self-hosted offline tiles (PMTiles) stay in M7.

## 5. Tasks

| # | Task | Acceptance check | PR |
|---|------|------------------|----|
| 1 | Contracts: `packages/contracts` uv workspace member with `Telemetry` + `TelemetryMessage`; inject into OpenAPI `components.schemas`; regenerate TS types; API Dockerfile and compose watch include the package | `just api-check` passes; tests: valid sample → expected JSON, heading 400 rejected; `schema.d.ts` has the message types | |
| 2 | Fake drone: `VehicleLink` Protocol, `FakeVehicle.state_at`, `telemetry()` async generator, `FAKE_HOME_*` settings | Tests: position/heading at t=0 and after a quarter lap, battery cycle restarts, stream yields 3 ordered samples | |
| 3 | `TelemetryBroadcaster` + reader task in `lifespan` (start, cancel, retry after 1 s) | Tests: two subscribers get the same messages; full queue keeps newest 10; reader recovers after the stream raises | |
| 4 | WS endpoint `/api/ws/telemetry` (TaskGroup send/receive, unsubscribe in `finally`); Vite proxy `ws: true` | `TestClient` + scripted vehicle: two clients receive the same messages, disconnect removes the subscription; messages visible in browser devtools | |
| 5 | `TelemetryClient` + Zustand store + status indicator + `useTelemetryConnection()` | Vitest with fake timers and fake WebSocket: backoff grows/caps/resets, stale after 1 s, forced reconnect after 5 s; demo step 3 | |
| 6 | HUD: altitude, speed, heading, battery via selectors; greyed when link lost | Component test: store values render; greyed state | |
| 7 | Map: `maplibre-gl`, rotated drone icon, 30 s trail, home marker, optional `VITE_BASEMAP_URL` raster layer + attribution | Unit test for trail logic (append, keep last 300); demo steps 1–2 | |
| 8 | Close-out: README (env vars, demo), retro, tick ROADMAP | Demo passes from a fresh clone | |

## 6. Open questions

- **Smoothing between samples** (interpolating the marker between 10 Hz updates): not in M1; revisit if motion looks
  jumpy.
- **Vehicle link status** ("API reachable, drone silent"): M5 adds a backend-reported link state; until then the
  client's 5 s forced reconnect would churn in that case.
- **Catching TaskGroup errors** (`except*` on the `ExceptionGroup`): exact handling settled in task 4.
- **Drop policy for event messages**: M4 adds a separate path for messages that must not be dropped.

## 7. As built / retro

_Filled at close-out._
