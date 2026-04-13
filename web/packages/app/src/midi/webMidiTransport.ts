import type { Transport } from '@mft-editor/core';

const DEVICE_NAME_PATTERN = 'midi fighter twister';

export interface WebMidiPorts {
  input: MIDIInput;
  output: MIDIOutput;
}

export function webMidiSupported(): boolean {
  return typeof navigator !== 'undefined' && 'requestMIDIAccess' in navigator;
}

export async function requestWebMidiAccess(): Promise<MIDIAccess> {
  if (!webMidiSupported()) {
    throw new Error(
      'Web MIDI API is not available. Use a Chromium-based browser (Chrome, Edge, Arc, Brave, Opera).',
    );
  }
  return navigator.requestMIDIAccess({ sysex: true });
}

export function findMftPorts(access: MIDIAccess): WebMidiPorts | null {
  let input: MIDIInput | null = null;
  let output: MIDIOutput | null = null;
  for (const port of access.inputs.values()) {
    if (port.name && port.name.toLowerCase().includes(DEVICE_NAME_PATTERN)) {
      input = port;
      break;
    }
  }
  for (const port of access.outputs.values()) {
    if (port.name && port.name.toLowerCase().includes(DEVICE_NAME_PATTERN)) {
      output = port;
      break;
    }
  }
  return input && output ? { input, output } : null;
}

export function listInputs(access: MIDIAccess): MIDIInput[] {
  return Array.from(access.inputs.values());
}

export function listOutputs(access: MIDIAccess): MIDIOutput[] {
  return Array.from(access.outputs.values());
}

type Listener = (data: readonly number[]) => void;

/**
 * Web MIDI adapter implementing the core Transport interface. The core layer
 * works in payloads WITHOUT F0/F7 framing; this adapter adds the framing on
 * send and strips it on receive.
 */
export class WebMidiTransport implements Transport {
  readonly name: string;
  connected = true;

  private readonly input: MIDIInput;
  private readonly output: MIDIOutput;
  private listeners = new Set<Listener>();
  private readonly boundHandler: (event: Event) => void;

  constructor(ports: WebMidiPorts) {
    this.input = ports.input;
    this.output = ports.output;
    this.name = this.input.name ?? 'Web MIDI Device';
    this.boundHandler = (event: Event) => {
      this.handleMessage(event as MIDIMessageEvent);
    };
    this.input.addEventListener('midimessage', this.boundHandler);
  }

  send(data: readonly number[]): void {
    const framed = new Uint8Array(data.length + 2);
    framed[0] = 0xf0;
    framed.set(data, 1);
    framed[framed.length - 1] = 0xf7;
    this.output.send(framed);
  }

  onMessage(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  close(): void {
    this.input.removeEventListener('midimessage', this.boundHandler);
    this.listeners.clear();
    this.connected = false;
  }

  private handleMessage(event: MIDIMessageEvent): void {
    const data = event.data;
    if (!data || data.length < 2) return;
    if (data[0] !== 0xf0) return;
    let end = data.length;
    if (data[end - 1] === 0xf7) end -= 1;
    const payload: number[] = [];
    for (let i = 1; i < end; i++) payload.push(data[i]!);
    for (const listener of this.listeners) {
      listener(payload);
    }
  }
}
