<script lang="ts">
  import { NUM_ENCODERS } from '@mft-editor/core';
  import { selectionStore } from '../stores/selectionStore.svelte.js';

  const encoderIndices = Array.from({ length: NUM_ENCODERS }, (_, i) => i);

  function toggle(idx: number): void {
    const next = new Set(selectionStore.multiSelection);
    if (next.has(idx)) next.delete(idx);
    else next.add(idx);
    selectionStore.multiSelection = next;
  }

  function selectAll(): void {
    selectionStore.multiSelection = new Set(encoderIndices);
  }

  function clearAll(): void {
    selectionStore.multiSelection = new Set();
  }

  const selectedCount = $derived(selectionStore.multiSelection.size);
</script>

<section class="panel">
  <header class="head">
    <h2>Multi-Edit</h2>
    <span class="count">
      {#if selectedCount === 0}
        Off
      {:else}
        {selectedCount} selected — edits apply to all
      {/if}
    </span>
  </header>
  <div class="actions">
    <button type="button" onclick={selectAll}>Select All</button>
    <button type="button" onclick={clearAll}>Clear</button>
  </div>
  <div class="grid">
    {#each encoderIndices as idx}
      <label class="item" class:selected={selectionStore.multiSelection.has(idx)}>
        <input
          type="checkbox"
          checked={selectionStore.multiSelection.has(idx)}
          onchange={() => toggle(idx)}
        />
        Enc {idx + 1}
      </label>
    {/each}
  </div>
</section>

<style>
  .panel {
    background: var(--bg-panel);
    border-radius: 6px;
    padding: 14px;
  }

  .head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 10px;
    gap: 10px;
  }

  .count {
    font-size: 11px;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .actions {
    display: flex;
    gap: 6px;
    margin-bottom: 10px;
  }

  .actions button {
    flex: 1;
    font-size: 11px;
    padding: 4px 8px;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 4px;
  }

  .item {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 6px;
    background: var(--bg-raised);
    border-radius: 3px;
    font-size: 11px;
    cursor: pointer;
    color: var(--fg-dim);
    text-transform: none;
    letter-spacing: 0;
  }

  .item.selected {
    background: var(--bg-hover);
    color: var(--fg);
  }

  .item input {
    width: auto;
    margin: 0;
    accent-color: var(--accent);
  }
</style>
