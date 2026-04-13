<script lang="ts">
  import { SideSwAction } from '@mft-editor/core';
  import { configStore } from '../stores/configStore.svelte.js';

  const cfg = $derived(configStore.config.global_config);

  function update<K extends keyof typeof cfg>(field: K, value: (typeof cfg)[K]): void {
    configStore.updateGlobal({ [field]: value } as Partial<typeof cfg>);
  }

  function num(field: keyof typeof cfg, event: Event): void {
    const value = Number((event.target as HTMLInputElement).value);
    update(field, value as (typeof cfg)[typeof field]);
  }

  function sel(field: keyof typeof cfg, event: Event): void {
    const value = Number((event.target as HTMLSelectElement).value);
    update(field, value as (typeof cfg)[typeof field]);
  }

  const sideActionOptions = [
    { value: SideSwAction.CC_HOLD, label: 'CC Hold' },
    { value: SideSwAction.CC_TOGGLE, label: 'CC Toggle' },
    { value: SideSwAction.NOTE_HOLD, label: 'Note Hold' },
    { value: SideSwAction.NOTE_TOGGLE, label: 'Note Toggle' },
    { value: SideSwAction.SHIFT_PAGE_1, label: 'Shift Page 1' },
    { value: SideSwAction.SHIFT_PAGE_2, label: 'Shift Page 2' },
    { value: SideSwAction.BANK_UP, label: 'Bank Up' },
    { value: SideSwAction.BANK_DOWN, label: 'Bank Down' },
    { value: SideSwAction.BANK_1, label: 'Bank 1' },
    { value: SideSwAction.BANK_2, label: 'Bank 2' },
    { value: SideSwAction.BANK_3, label: 'Bank 3' },
    { value: SideSwAction.BANK_4, label: 'Bank 4' },
    { value: SideSwAction.CYCLE_BANK, label: 'Cycle Bank' },
  ];

  const sideFuncFields = [
    'side_func_1',
    'side_func_2',
    'side_func_3',
    'side_func_4',
    'side_func_5',
    'side_func_6',
  ] as const;
</script>

<section class="panel">
  <h2>Global Settings</h2>

  <div class="grid">
    <div class="group">
      <h3>MIDI</h3>
      <div class="row">
        <label for="g-ch">Default channel (1-16)</label>
        <input
          id="g-ch"
          type="number"
          min="1"
          max="16"
          value={cfg.midi_channel + 1}
          oninput={(e) => update('midi_channel', Number((e.target as HTMLInputElement).value) - 1)}
        />
      </div>
      <div class="row">
        <label>
          <input
            type="checkbox"
            checked={cfg.side_is_banked === 1}
            onchange={(e) =>
              update('side_is_banked', (e.target as HTMLInputElement).checked ? 1 : 0)}
          />
          Side switches banked
        </label>
      </div>
    </div>

    <div class="group">
      <h3>Brightness</h3>
      <div class="row">
        <label for="g-rgb">RGB ({cfg.rgb_brightness})</label>
        <input
          id="g-rgb"
          type="range"
          min="0"
          max="127"
          value={cfg.rgb_brightness}
          oninput={(e) => num('rgb_brightness', e)}
        />
      </div>
      <div class="row">
        <label for="g-ind">Indicator ({cfg.ind_brightness})</label>
        <input
          id="g-ind"
          type="range"
          min="0"
          max="127"
          value={cfg.ind_brightness}
          oninput={(e) => num('ind_brightness', e)}
        />
      </div>
    </div>

    <div class="group">
      <h3>Super Knob Range</h3>
      <div class="row">
        <label for="g-sks">Start ({cfg.super_knob_start})</label>
        <input
          id="g-sks"
          type="range"
          min="0"
          max="127"
          value={cfg.super_knob_start}
          oninput={(e) => num('super_knob_start', e)}
        />
      </div>
      <div class="row">
        <label for="g-ske">End ({cfg.super_knob_end})</label>
        <input
          id="g-ske"
          type="range"
          min="0"
          max="127"
          value={cfg.super_knob_end}
          oninput={(e) => num('super_knob_end', e)}
        />
      </div>
    </div>

    <div class="group side-funcs">
      <h3>Side Switch Functions</h3>
      {#each sideFuncFields as field, i}
        <div class="row">
          <label for={`sf-${i}`}>{i + 1}</label>
          <select
            id={`sf-${i}`}
            value={cfg[field]}
            onchange={(e) => sel(field, e)}
          >
            {#each sideActionOptions as opt}
              <option value={opt.value}>{opt.label}</option>
            {/each}
          </select>
        </div>
      {/each}
    </div>
  </div>
</section>

<style>
  .panel {
    background: var(--bg-panel);
    border-radius: 6px;
    padding: 16px;
  }

  h2 {
    margin-bottom: 14px;
  }

  h3 {
    font-size: 12px;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 10px;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  .group {
    background: var(--bg-raised);
    padding: 12px;
    border-radius: 4px;
  }

  .side-funcs {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
  }

  .side-funcs h3 {
    grid-column: 1 / -1;
    margin-bottom: 0;
  }

  .row {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-bottom: 8px;
  }

  .row:last-child {
    margin-bottom: 0;
  }

  .row label:has(input[type='checkbox']) {
    flex-direction: row;
    align-items: center;
    gap: 6px;
    color: var(--fg);
    text-transform: none;
    font-size: 13px;
    letter-spacing: 0;
    cursor: pointer;
  }

  input[type='range'] {
    width: 100%;
    accent-color: var(--accent);
  }
</style>
