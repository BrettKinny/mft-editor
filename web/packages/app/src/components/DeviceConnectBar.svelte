<script lang="ts">
  import {
    MockTransport,
    exportConfigJsonString,
    importConfig,
    pullDeviceConfig,
    pushDeviceConfig,
  } from '@mft-editor/core';
  import {
    WebMidiTransport,
    findMftPorts,
    requestWebMidiAccess,
  } from '../midi/webMidiTransport.js';
  import { configStore } from '../stores/configStore.svelte.js';
  import { connectionStore } from '../stores/connectionStore.svelte.js';

  let fileInput: HTMLInputElement;

  async function connect(): Promise<void> {
    connectionStore.setConnecting();
    try {
      const access = await requestWebMidiAccess();
      const ports = findMftPorts(access);
      if (!ports) {
        connectionStore.setError(
          'No Midi Fighter Twister found. Is it plugged in?',
        );
        return;
      }
      const transport = new WebMidiTransport(ports);
      connectionStore.setConnected(transport);
    } catch (err) {
      connectionStore.setError((err as Error).message);
    }
  }

  function connectMock(): void {
    const mock = new MockTransport();
    mock.config = { ...configStore.config };
    connectionStore.setConnected(mock);
  }

  function disconnect(): void {
    connectionStore.disconnect();
  }

  async function pull(): Promise<void> {
    const transport = connectionStore.transport;
    if (!transport) return;
    connectionStore.setBusy(true);
    try {
      const config = await pullDeviceConfig(transport);
      configStore.replace(config);
    } catch (err) {
      connectionStore.setError(`Pull failed: ${(err as Error).message}`);
    } finally {
      connectionStore.setBusy(false);
    }
  }

  async function push(): Promise<void> {
    const transport = connectionStore.transport;
    if (!transport) return;
    connectionStore.setBusy(true);
    try {
      await pushDeviceConfig(transport, configStore.config);
    } catch (err) {
      connectionStore.setError(`Push failed: ${(err as Error).message}`);
    } finally {
      connectionStore.setBusy(false);
    }
  }

  function save(): void {
    const json = exportConfigJsonString(configStore.config);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'mft-preset.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  async function onFileChange(event: Event): Promise<void> {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;
    try {
      const buffer = await file.arrayBuffer();
      const config = importConfig(new Uint8Array(buffer));
      configStore.replace(config);
    } catch (err) {
      connectionStore.setError(`Load failed: ${(err as Error).message}`);
    } finally {
      target.value = '';
    }
  }

  function openLoad(): void {
    fileInput.click();
  }
</script>

<header class="bar">
  <div class="brand">
    <h1>MFT Editor</h1>
    <span class="subtitle">web</span>
  </div>

  <div class="status">
    {#if connectionStore.status === 'connected'}
      <span class="dot ok"></span>
      <span>{connectionStore.deviceName}</span>
    {:else if connectionStore.status === 'connecting'}
      <span class="dot connecting"></span>
      <span>Connecting…</span>
    {:else if connectionStore.status === 'error'}
      <span class="dot err"></span>
      <span class="err-text">{connectionStore.error}</span>
    {:else}
      <span class="dot"></span>
      <span class="muted">Not connected</span>
    {/if}
  </div>

  <div class="actions">
    {#if connectionStore.status !== 'connected'}
      <button class="primary" onclick={connect}>Connect</button>
      <button onclick={connectMock}>Use mock</button>
    {:else}
      <button onclick={pull} disabled={connectionStore.busy}>Pull</button>
      <button onclick={push} disabled={connectionStore.busy}>Push</button>
      <button onclick={disconnect}>Disconnect</button>
    {/if}
    <button onclick={openLoad}>Load…</button>
    <button onclick={save}>Save</button>
    <input
      type="file"
      accept=".json,.mfs,application/json"
      bind:this={fileInput}
      onchange={onFileChange}
      style="display: none"
    />
  </div>
</header>

<style>
  .bar {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 10px 18px;
    background: var(--bg-panel);
    border-bottom: 1px solid var(--border);
  }

  .brand {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
  }

  h1 {
    font-size: 16px;
    font-weight: 600;
  }

  .subtitle {
    font-size: 11px;
    color: var(--fg-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
    min-width: 0;
  }

  .status span:not(.dot) {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--fg-muted);
    flex-shrink: 0;
  }

  .dot.ok {
    background: var(--success);
    box-shadow: 0 0 6px var(--success);
  }

  .dot.connecting {
    background: var(--warning);
    animation: pulse 1s ease-in-out infinite;
  }

  .dot.err {
    background: var(--error);
  }

  .err-text {
    color: var(--error);
  }

  .muted {
    color: var(--fg-muted);
  }

  .actions {
    display: flex;
    gap: 0.5rem;
  }

  @keyframes pulse {
    50% {
      opacity: 0.4;
    }
  }
</style>
