import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { describe, expect, it } from 'vitest';

import {
  encoderFromBytes,
  globalFromBytes,
  type DeviceConfig,
  type EncoderConfig,
  type GlobalConfig,
} from '../model.js';
import {
  exportConfigJson,
  importConfig,
  type PresetJson,
} from '../presetFile.js';
import {
  buildBulkPushEncoder,
  buildPushGlobal,
  parseEncoderPayload,
  parsePushGlobal,
  identifyMessage,
  CMD_PUSH_CONF,
  CMD_BULK_XFER,
} from '../sysex.js';

interface FixtureEncoderEntry {
  bank: number;
  encoder: number;
  messages: number[][];
}

interface Fixture {
  name: string;
  preset: PresetJson;
  sysex: {
    global: number[];
    encoders: FixtureEncoderEntry[];
  };
}

const HERE = dirname(fileURLToPath(import.meta.url));
const FIXTURES_DIR = resolve(HERE, '../../../../../tests/fixtures');

function loadFixtures(): Fixture[] {
  const files = readdirSync(FIXTURES_DIR).filter(
    (f) => f.endsWith('.json') && f !== 'index.json' && !f.startsWith('_'),
  );
  files.sort();
  return files.map((file) => {
    const raw = readFileSync(join(FIXTURES_DIR, file), 'utf-8');
    return JSON.parse(raw) as Fixture;
  });
}

function deviceConfigFromPreset(preset: PresetJson): DeviceConfig {
  const encoders: EncoderConfig[] = preset.encoders.map((bytes) => encoderFromBytes(bytes));
  const global_config: GlobalConfig = globalFromBytes(preset.global);
  return { encoders, global_config };
}

describe('byte-exact fixtures vs Python', () => {
  const fixtures = loadFixtures();

  if (fixtures.length === 0) {
    it.skip('no fixtures found — run `uv run python tests/generate_fixtures.py`', () => {});
    return;
  }

  for (const fixture of fixtures) {
    describe(fixture.name, () => {
      const config = deviceConfigFromPreset(fixture.preset);

      it('JSON preset exports byte-identically', () => {
        const exported = exportConfigJson(config);
        expect(exported).toEqual(fixture.preset);
      });

      it('JSON preset roundtrips via importConfig', () => {
        const jsonString = JSON.stringify(fixture.preset);
        const bytes = new TextEncoder().encode(jsonString);
        const imported = importConfig(bytes);
        expect(exportConfigJson(imported)).toEqual(fixture.preset);
      });

      it('build_push_global matches Python byte stream', () => {
        const built = buildPushGlobal(config.global_config);
        expect(built).toEqual(fixture.sysex.global);
      });

      it('parse_push_global decodes Python byte stream', () => {
        const ident = identifyMessage(fixture.sysex.global);
        expect(ident).not.toBeNull();
        expect(ident!.command).toBe(CMD_PUSH_CONF);
        const parsed = parsePushGlobal(ident!.payload);
        expect(parsed).toEqual(config.global_config);
      });

      it('build_bulk_push_encoder matches Python byte stream (all 64)', () => {
        for (const entry of fixture.sysex.encoders) {
          const cfg = config.encoders[entry.bank * 16 + entry.encoder]!;
          const built = buildBulkPushEncoder(entry.bank, entry.encoder, cfg);
          expect({
            bank: entry.bank,
            encoder: entry.encoder,
            messages: built,
          }).toEqual(entry);
        }
      });

      it('parse_encoder_payload decodes Python byte stream (all 64)', () => {
        for (const entry of fixture.sysex.encoders) {
          const payload: number[] = [];
          for (const msg of entry.messages) {
            const ident = identifyMessage(msg);
            expect(ident).not.toBeNull();
            expect(ident!.command).toBe(CMD_BULK_XFER);
            const size = ident!.payload[4]!;
            payload.push(...ident!.payload.slice(5, 5 + size));
          }
          const parsed = parseEncoderPayload(payload);
          const expected = config.encoders[entry.bank * 16 + entry.encoder]!;
          expect(parsed).toEqual(expected);
        }
      });
    });
  }
});
