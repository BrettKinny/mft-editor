import {
  NUM_ENCODERS,
  makeDefaultDeviceConfig,
  type DeviceConfig,
  type EncoderConfig,
  type GlobalConfig,
} from '@mft-editor/core';

class ConfigStore {
  config = $state<DeviceConfig>(makeDefaultDeviceConfig());

  replace(next: DeviceConfig): void {
    this.config = next;
  }

  updateGlobal(patch: Partial<GlobalConfig>): void {
    this.config = {
      ...this.config,
      global_config: { ...this.config.global_config, ...patch },
    };
  }

  updateEncoder(bank: number, encoder: number, patch: Partial<EncoderConfig>): void {
    const idx = bank * NUM_ENCODERS + encoder;
    const encoders = this.config.encoders.slice();
    encoders[idx] = { ...encoders[idx]!, ...patch };
    this.config = { ...this.config, encoders };
  }

  updateEncoderField<K extends keyof EncoderConfig>(
    bank: number,
    encoder: number,
    field: K,
    value: EncoderConfig[K],
  ): void {
    this.updateEncoder(bank, encoder, { [field]: value } as Partial<EncoderConfig>);
  }

  updateEncoders(
    bank: number,
    encoderIndices: readonly number[],
    patch: Partial<EncoderConfig>,
  ): void {
    const encoders = this.config.encoders.slice();
    for (const enc of encoderIndices) {
      const idx = bank * NUM_ENCODERS + enc;
      encoders[idx] = { ...encoders[idx]!, ...patch };
    }
    this.config = { ...this.config, encoders };
  }

  updateEncodersField<K extends keyof EncoderConfig>(
    bank: number,
    encoderIndices: readonly number[],
    field: K,
    value: EncoderConfig[K],
  ): void {
    this.updateEncoders(bank, encoderIndices, { [field]: value } as Partial<EncoderConfig>);
  }

  getEncoder(bank: number, encoder: number): EncoderConfig {
    return this.config.encoders[bank * NUM_ENCODERS + encoder]!;
  }
}

export const configStore = new ConfigStore();
