<script lang="ts">
  import {
    DisplayType,
    EncMoveType,
    EncSwActionType,
    MidiType,
    type EncoderConfig,
  } from '@mft-editor/core';
  import ColorPicker from './ColorPicker.svelte';
  import IndicatorPreview from './IndicatorPreview.svelte';
  import { configStore } from '../stores/configStore.svelte.js';
  import { selectionStore } from '../stores/selectionStore.svelte.js';

  const cfg = $derived(configStore.getEncoder(selectionStore.bank, selectionStore.encoder));

  const targetCount = $derived(selectionStore.multiSelection.size || 1);

  function update<K extends keyof EncoderConfig>(field: K, value: EncoderConfig[K]): void {
    const targets = selectionStore.editTargets();
    configStore.updateEncodersField(selectionStore.bank, targets, field, value);
  }

  function onNumberInput(field: keyof EncoderConfig, event: Event): void {
    update(field, Number((event.target as HTMLInputElement).value) as EncoderConfig[typeof field]);
  }

  function onSelect(field: keyof EncoderConfig, event: Event): void {
    update(field, Number((event.target as HTMLSelectElement).value) as EncoderConfig[typeof field]);
  }

  function onCheckbox(field: keyof EncoderConfig, event: Event): void {
    update(
      field,
      ((event.target as HTMLInputElement).checked ? 1 : 0) as EncoderConfig[typeof field],
    );
  }

  function onColorChange(mode: 'active' | 'inactive' | 'detent', index: number): void {
    if (mode === 'active') update('active_color', index);
    else if (mode === 'inactive') update('inactive_color', index);
    else update('detent_color', index);
  }

  const midiTypeOptions = [
    { value: MidiType.NOTE, label: 'Note' },
    { value: MidiType.CC, label: 'CC' },
    { value: MidiType.REL_ENC, label: 'Rel. Encoder' },
    { value: MidiType.SWITCH_VEL_CONTROL, label: 'Switch vel.' },
    { value: MidiType.REL_ENC_MOUSE_DRAG, label: 'Rel. Mouse drag' },
    { value: MidiType.REL_ENC_MOUSE_SCROLL, label: 'Rel. Mouse scroll' },
  ];

  const switchActionOptions = [
    { value: EncSwActionType.CC_HOLD, label: 'CC Hold' },
    { value: EncSwActionType.CC_TOGGLE, label: 'CC Toggle' },
    { value: EncSwActionType.NOTE_HOLD, label: 'Note Hold' },
    { value: EncSwActionType.NOTE_TOGGLE, label: 'Note Toggle' },
    { value: EncSwActionType.RESET_VALUE, label: 'Reset Value' },
    { value: EncSwActionType.FINE_ADJUST, label: 'Fine Adjust' },
    { value: EncSwActionType.SHIFT_HOLD, label: 'Shift Hold' },
    { value: EncSwActionType.SHIFT_TOGGLE, label: 'Shift Toggle' },
  ];

  const movementOptions = [
    { value: EncMoveType.DIRECT, label: 'Direct' },
    { value: EncMoveType.RESPONSIVE, label: 'Responsive' },
    { value: EncMoveType.VELOCITY_SENSITIVE, label: 'Velocity Sensitive' },
  ];

  const displayOptions = [
    { value: DisplayType.DOT, label: 'Dot' },
    { value: DisplayType.BAR, label: 'Bar' },
    { value: DisplayType.BLENDED_BAR, label: 'Blended Bar' },
    { value: DisplayType.BLENDED_DOT, label: 'Blended Dot' },
  ];
</script>

<section class="panel">
  <header class="head">
    <h2>
      Encoder {selectionStore.encoder + 1} · Bank {selectionStore.bank + 1}
    </h2>
    {#if targetCount > 1}
      <span class="multi-pill">applying to {targetCount}</span>
    {/if}
  </header>

  <div class="grid">
    <div class="group">
      <h3>Encoder (turn)</h3>
      <div class="row">
        <label for="enc-type">Type</label>
        <select
          id="enc-type"
          value={cfg.encoder_midi_type}
          onchange={(e) => onSelect('encoder_midi_type', e)}
        >
          {#each midiTypeOptions as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
      <div class="row">
        <label for="enc-ch">Channel (1-16)</label>
        <input
          id="enc-ch"
          type="number"
          min="1"
          max="16"
          value={cfg.encoder_midi_channel + 1}
          oninput={(e) =>
            update('encoder_midi_channel', Number((e.target as HTMLInputElement).value) - 1)}
        />
      </div>
      <div class="row">
        <label for="enc-num">Number (0-127)</label>
        <input
          id="enc-num"
          type="number"
          min="0"
          max="127"
          value={cfg.encoder_midi_number}
          oninput={(e) => onNumberInput('encoder_midi_number', e)}
        />
      </div>
      <div class="row">
        <label for="enc-move">Movement</label>
        <select
          id="enc-move"
          value={cfg.movement}
          onchange={(e) => onSelect('movement', e)}
        >
          {#each movementOptions as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
      <div class="row">
        <label for="enc-shift">Shift channel (1-16)</label>
        <input
          id="enc-shift"
          type="number"
          min="1"
          max="16"
          value={cfg.encoder_shift_midi_channel + 1}
          oninput={(e) =>
            update('encoder_shift_midi_channel', Number((e.target as HTMLInputElement).value) - 1)}
        />
      </div>
    </div>

    <div class="group">
      <h3>Switch (press)</h3>
      <div class="row">
        <label for="sw-type">Type</label>
        <select
          id="sw-type"
          value={cfg.switch_midi_type}
          onchange={(e) => onSelect('switch_midi_type', e)}
        >
          {#each midiTypeOptions as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
      <div class="row">
        <label for="sw-action">Action</label>
        <select
          id="sw-action"
          value={cfg.switch_action_type}
          onchange={(e) => onSelect('switch_action_type', e)}
        >
          {#each switchActionOptions as opt}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>
      <div class="row">
        <label for="sw-ch">Channel (1-16)</label>
        <input
          id="sw-ch"
          type="number"
          min="1"
          max="16"
          value={cfg.switch_midi_channel + 1}
          oninput={(e) =>
            update('switch_midi_channel', Number((e.target as HTMLInputElement).value) - 1)}
        />
      </div>
      <div class="row">
        <label for="sw-num">Number (0-127)</label>
        <input
          id="sw-num"
          type="number"
          min="0"
          max="127"
          value={cfg.switch_midi_number}
          oninput={(e) => onNumberInput('switch_midi_number', e)}
        />
      </div>
    </div>

    <div class="group">
      <h3>Indicator</h3>
      <div class="indicator-row">
        <IndicatorPreview
          displayType={cfg.indicator_display_type}
          activeColor={cfg.active_color}
          inactiveColor={cfg.inactive_color}
        />
        <div class="indicator-controls">
          <div class="row">
            <label for="ind-disp">Display type</label>
            <select
              id="ind-disp"
              value={cfg.indicator_display_type}
              onchange={(e) => onSelect('indicator_display_type', e)}
            >
              {#each displayOptions as opt}
                <option value={opt.value}>{opt.label}</option>
              {/each}
            </select>
          </div>
          <div class="row">
            <label>
              <input
                type="checkbox"
                checked={cfg.has_detent === 1}
                onchange={(e) => onCheckbox('has_detent', e)}
              />
              Has detent
            </label>
          </div>
          <div class="row">
            <label>
              <input
                type="checkbox"
                checked={cfg.is_super_knob === 1}
                onchange={(e) => onCheckbox('is_super_knob', e)}
              />
              Super knob
            </label>
          </div>
        </div>
      </div>
    </div>

    <div class="group colors">
      <h3>Colors</h3>
      <ColorPicker
        active={cfg.active_color}
        inactive={cfg.inactive_color}
        detent={cfg.detent_color}
        onchange={onColorChange}
      />
    </div>
  </div>
</section>

<style>
  .panel {
    background: var(--bg-panel);
    border-radius: 6px;
    padding: 16px;
  }

  .head {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 14px;
  }

  .multi-pill {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    background: var(--accent);
    color: #0a1013;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 600;
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
    gap: 14px;
  }

  .group {
    background: var(--bg-raised);
    padding: 12px;
    border-radius: 4px;
  }

  .group.colors {
    grid-column: 1 / -1;
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

  .indicator-row {
    display: flex;
    gap: 14px;
    align-items: flex-start;
  }

  .indicator-controls {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
</style>
