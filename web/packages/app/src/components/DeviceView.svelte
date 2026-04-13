<script lang="ts">
  import { NUM_BANKS, NUM_ENCODERS, colorToHex } from '@mft-editor/core';
  import { configStore } from '../stores/configStore.svelte.js';
  import { selectionStore } from '../stores/selectionStore.svelte.js';

  const banks = Array.from({ length: NUM_BANKS }, (_, i) => i);
  const encoderIndices = Array.from({ length: NUM_ENCODERS }, (_, i) => i);

  function select(encoder: number): void {
    selectionStore.select(selectionStore.bank, encoder);
  }

  function cellStyle(bank: number, enc: number): string {
    const cfg = configStore.config.encoders[bank * NUM_ENCODERS + enc]!;
    return `background: ${colorToHex(cfg.active_color)};`;
  }
</script>

<section class="device-view">
  <div class="banks">
    {#each banks as b}
      <button
        class="bank"
        class:active={selectionStore.bank === b}
        onclick={() => selectionStore.setBank(b)}
      >
        Bank {b + 1}
      </button>
    {/each}
  </div>

  <div class="grid">
    {#each encoderIndices as enc}
      {@const cfg = configStore.config.encoders[
        selectionStore.bank * NUM_ENCODERS + enc
      ]}
      <button
        class="cell"
        class:selected={selectionStore.encoder === enc}
        style={cellStyle(selectionStore.bank, enc)}
        onclick={() => select(enc)}
        title={`Encoder ${enc + 1} — CH${cfg!.encoder_midi_channel + 1} CC${cfg!.encoder_midi_number}`}
      >
        <span class="num">{enc + 1}</span>
      </button>
    {/each}
  </div>
</section>

<style>
  .device-view {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 14px;
    background: var(--bg-panel);
    border-radius: 6px;
  }

  .banks {
    display: flex;
    gap: 6px;
  }

  .bank {
    padding: 5px 12px;
    font-size: 12px;
  }

  .bank.active {
    background: var(--accent);
    color: #0a1013;
    border-color: var(--accent);
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
    aspect-ratio: 1;
  }

  .cell {
    padding: 0;
    border: 2px solid var(--border);
    border-radius: 50%;
    position: relative;
    aspect-ratio: 1;
    cursor: pointer;
    transition: transform 0.08s ease, border-color 0.08s ease;
  }

  .cell:hover {
    transform: scale(1.04);
  }

  .cell.selected {
    border-color: var(--fg);
    box-shadow: 0 0 0 2px var(--accent);
  }

  .num {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    color: #000;
    font-weight: 700;
    font-size: 13px;
    text-shadow: 0 0 3px rgba(255, 255, 255, 0.6);
    mix-blend-mode: luminosity;
  }
</style>
