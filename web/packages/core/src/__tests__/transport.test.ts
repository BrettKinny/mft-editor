import { describe, expect, it } from 'vitest';

import { MockTransport } from '../mockTransport.js';
import {
  getEncoder,
  makeDefaultDeviceConfig,
  makeDefaultEncoderConfig,
  type EncoderConfig,
} from '../model.js';
import {
  pullDeviceConfig,
  pullEncoder,
  pullGlobal,
  pushDeviceConfig,
} from '../transport.js';

describe('MockTransport roundtrip via orchestration', () => {
  it('pullGlobal returns current global config', async () => {
    const cfg = makeDefaultDeviceConfig();
    cfg.global_config.midi_channel = 7;
    cfg.global_config.rgb_brightness = 44;
    const transport = new MockTransport(cfg);

    const pulled = await pullGlobal(transport);
    expect(pulled.midi_channel).toBe(7);
    expect(pulled.rgb_brightness).toBe(44);
  });

  it('pullEncoder returns stored encoder config', async () => {
    const cfg = makeDefaultDeviceConfig();
    const custom: EncoderConfig = {
      ...makeDefaultEncoderConfig(),
      active_color: 99,
      encoder_midi_number: 42,
      switch_midi_channel: 3,
    };
    cfg.encoders[1 * 16 + 3] = custom;
    const transport = new MockTransport(cfg);

    const pulled = await pullEncoder(transport, 1, 3);
    expect(pulled.active_color).toBe(99);
    expect(pulled.encoder_midi_number).toBe(42);
    expect(pulled.switch_midi_channel).toBe(3);
  });

  it('full pullDeviceConfig roundtrip matches push source', async () => {
    const source = makeDefaultDeviceConfig();
    source.global_config.midi_channel = 9;
    source.global_config.ind_brightness = 55;
    source.encoders[0]!.active_color = 10;
    source.encoders[17]!.encoder_midi_number = 77;
    source.encoders[63]!.is_super_knob = 1;

    // Push into an empty mock, then pull back out.
    const sink = new MockTransport();
    await pushDeviceConfig(sink, source);
    const pulled = await pullDeviceConfig(sink);

    expect(pulled.global_config.midi_channel).toBe(9);
    expect(pulled.global_config.ind_brightness).toBe(55);
    expect(getEncoder(pulled, 0, 0).active_color).toBe(10);
    expect(getEncoder(pulled, 1, 1).encoder_midi_number).toBe(77);
    expect(getEncoder(pulled, 3, 15).is_super_knob).toBe(1);
  }, 20000);
});
