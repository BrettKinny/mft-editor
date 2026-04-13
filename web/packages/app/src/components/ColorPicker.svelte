<script lang="ts">
  import { COLOR_MAP, colorToHex } from '@mft-editor/core';

  type Mode = 'active' | 'inactive' | 'detent';

  interface Props {
    active: number;
    inactive: number;
    detent: number;
    onchange: (mode: Mode, index: number) => void;
  }

  let { active, inactive, detent, onchange }: Props = $props();

  let mode = $state<Mode>('active');

  const currentForMode = $derived.by(() => {
    if (mode === 'active') return active;
    if (mode === 'inactive') return inactive;
    return detent;
  });

  function selectColor(index: number): void {
    onchange(mode, index);
  }

  const paletteIndices = Array.from({ length: COLOR_MAP.length }, (_, i) => i);
</script>

<div class="picker">
  <div class="modes">
    <button
      type="button"
      class="mode"
      class:active={mode === 'active'}
      onclick={() => (mode = 'active')}
    >
      <span class="swatch" style={`background: ${colorToHex(active)}`}></span>
      <span class="label">Active</span>
    </button>
    <button
      type="button"
      class="mode"
      class:active={mode === 'inactive'}
      onclick={() => (mode = 'inactive')}
    >
      <span class="swatch" style={`background: ${colorToHex(inactive)}`}></span>
      <span class="label">Inactive</span>
    </button>
    <button
      type="button"
      class="mode"
      class:active={mode === 'detent'}
      onclick={() => (mode = 'detent')}
    >
      <span class="swatch" style={`background: ${colorToHex(detent)}`}></span>
      <span class="label">Detent</span>
    </button>
  </div>

  <div class="palette">
    {#each paletteIndices as idx}
      <button
        type="button"
        class="cell"
        class:selected={currentForMode === idx}
        style={`background: ${colorToHex(idx)}`}
        title={`Color ${idx}`}
        onclick={() => selectColor(idx)}
        aria-label={`Color ${idx}`}
      ></button>
    {/each}
  </div>
</div>

<style>
  .picker {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .modes {
    display: flex;
    gap: 6px;
  }

  .mode {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    color: var(--fg-dim);
  }

  .mode.active {
    background: var(--bg-hover);
    border-color: var(--fg-muted);
    color: var(--fg);
  }

  .mode .swatch {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 1px solid #000;
    flex-shrink: 0;
  }

  .mode .label {
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 11px;
  }

  .palette {
    display: grid;
    grid-template-columns: repeat(18, 1fr);
    gap: 2px;
    padding: 4px;
    background: var(--bg-raised);
    border-radius: 4px;
  }

  .cell {
    aspect-ratio: 1;
    padding: 0;
    border: 1px solid rgba(0, 0, 0, 0.4);
    border-radius: 2px;
    cursor: pointer;
    min-width: 0;
    transition: transform 0.08s ease;
  }

  .cell:hover {
    transform: scale(1.25);
    z-index: 1;
    border-color: rgba(255, 255, 255, 0.6);
  }

  .cell.selected {
    outline: 2px solid var(--fg);
    outline-offset: 0;
    z-index: 1;
  }
</style>
