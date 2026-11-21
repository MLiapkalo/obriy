import type { StoreApi } from 'zustand/vanilla';
import type { components } from '../api/schema';
import type { TelemetryState } from './store';

export type TelemetryMessage = components['schemas']['TelemetryMessage'];

function isTelemetryMessage(value: unknown): value is TelemetryMessage {
  return typeof value === 'object' && value !== null && 'type' in value && value.type === 'telemetry';
}

export const BACKOFF_DELAY_BASE_MS = 500;
export const BACKOFF_DELAY_MAX_MS = 10_000;
export const STALE_AFTER_MS = 1_000;
export const RECONNECT_AFTER_MS = 5_000;

export function backoffDelayMs(attempt: number, random: () => number): number {
  // random is used for jittering the backoff delay
  return Math.min(BACKOFF_DELAY_MAX_MS, BACKOFF_DELAY_BASE_MS * 2 ** attempt) * random();
}

export class TelemetryClient {
  private readonly url: string;
  private readonly store: StoreApi<TelemetryState>;
  private ws: WebSocket | null = null;
  private abortController: AbortController | null = null;
  private running: boolean = false;
  private attempt: number = 0;
  private retryTimeout: ReturnType<typeof setTimeout> | null = null;
  private silenceTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(url: string, store: StoreApi<TelemetryState>) {
    this.url = url;
    this.store = store;
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.connect();
  }

  stop(): void {
    this.running = false;
    if (this.retryTimeout) {
      clearTimeout(this.retryTimeout);
      this.retryTimeout = null;
    }
    this.closeSocket();
  }

  private connect(): void {
    this.store.setState({ status: 'connecting' });

    this.ws = new WebSocket(this.url);
    this.abortController = new AbortController();

    this.ws.addEventListener(
      'open',
      () => {
        this.attempt = 0;
        this.store.setState({ status: 'live' });
      },
      { signal: this.abortController.signal },
    );

    this.ws.addEventListener(
      'message',
      (event: MessageEvent<string>) => {
        const message: unknown = JSON.parse(event.data);
        if (!isTelemetryMessage(message)) return;
        // telemetry silence watchdog, resets on every valid telemetry message received
        this.armWatchdog();
        this.store.setState({
          status: 'live',
          telemetry: message.payload,
        });
      },
      { signal: this.abortController.signal },
    );

    this.ws.addEventListener('close', () => this.handleConnectionLost(), { signal: this.abortController.signal });

    this.armWatchdog();
  }

  private closeSocket(): void {
    this.abortController?.abort();
    this.ws?.close();
    this.ws = null;
    this.abortController = null;
    this.clearSilenceTimer();
  }

  private handleConnectionLost(): void {
    this.store.setState({ status: 'lost' });
    this.closeSocket();

    if (!this.running) return;

    this.retryTimeout = setTimeout(
      () => {
        this.retryTimeout = null;
        this.attempt++;
        this.connect();
      },
      backoffDelayMs(this.attempt, Math.random),
    );
  }

  private armWatchdog(): void {
    this.clearSilenceTimer();
    this.silenceTimer = setTimeout(() => {
      // mark the connection as stale after 1s of silence
      this.store.setState((state) => ({
        status: state.status === 'live' ? 'stale' : state.status,
      }));
      // if silence continues for 5s - attempt to reconnect
      this.silenceTimer = setTimeout(() => this.handleConnectionLost(), RECONNECT_AFTER_MS - STALE_AFTER_MS);
    }, STALE_AFTER_MS);
  }

  private clearSilenceTimer(): void {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
  }
}
