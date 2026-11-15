import type { StoreApi } from 'zustand/vanilla';
import type { components } from '../api/schema';
import type { TelemetryState } from './store';

export type TelemetryMessage = components['schemas']['TelemetryMessage'];

function isTelemetryMessage(value: unknown): value is TelemetryMessage {
  return typeof value === 'object' && value !== null && 'type' in value && value.type === 'telemetry';
}

export class TelemetryClient {
  private readonly url: string;
  private readonly store: StoreApi<TelemetryState>;
  private ws: WebSocket | null = null;
  private abortController: AbortController | null = null;

  constructor(url: string, store: StoreApi<TelemetryState>) {
    this.url = url;
    this.store = store;
  }

  start(): void {
    if (this.ws) return;
    this.connect();
  }

  stop(): void {
    this.closeSocket();
  }

  private connect(): void {
    this.store.setState({ status: 'connecting' });

    this.ws = new WebSocket(this.url);
    this.abortController = new AbortController();

    this.ws.addEventListener(
      'message',
      (event: MessageEvent<string>) => {
        const message: unknown = JSON.parse(event.data);
        if (!isTelemetryMessage(message)) return;
        this.store.setState({
          status: 'live',
          telemetry: message.payload,
        });
      },
      { signal: this.abortController.signal },
    );

    this.ws.addEventListener(
      'close',
      () => {
        this.store.setState({ status: 'lost' });
      },
      { signal: this.abortController.signal },
    );
  }

  private closeSocket(): void {
    this.abortController?.abort();
    this.ws?.close();
    this.ws = null;
    this.abortController = null;
  }
}
