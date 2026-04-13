import type { Transport } from '@mft-editor/core';

type Status = 'disconnected' | 'connecting' | 'connected' | 'error';

class ConnectionStore {
  transport = $state<Transport | null>(null);
  status = $state<Status>('disconnected');
  error = $state<string | null>(null);
  deviceName = $state<string>('');
  busy = $state<boolean>(false);

  setConnecting(): void {
    this.status = 'connecting';
    this.error = null;
  }

  setConnected(transport: Transport): void {
    this.transport = transport;
    this.deviceName = transport.name;
    this.status = 'connected';
    this.error = null;
  }

  setError(message: string): void {
    this.status = 'error';
    this.error = message;
    this.busy = false;
  }

  disconnect(): void {
    if (this.transport) {
      try {
        this.transport.close();
      } catch {
        // noop
      }
    }
    this.transport = null;
    this.deviceName = '';
    this.status = 'disconnected';
    this.error = null;
    this.busy = false;
  }

  setBusy(value: boolean): void {
    this.busy = value;
  }
}

export const connectionStore = new ConnectionStore();
