<script lang="ts">
  import { DisplayType, COLOR_MAP } from '@mft-editor/core';

  interface Props {
    displayType: number;
    activeColor: number;
    inactiveColor: number;
    value?: number;
  }

  let { displayType, activeColor, inactiveColor, value = 80 }: Props = $props();

  const NUM_LEDS = 11;
  const START_ANGLE = 225;
  const SWEEP = 270;
  const RADIUS = 42;
  const CX = 50;
  const CY = 50;

  function rgb(index: number): readonly [number, number, number] {
    return COLOR_MAP[index & 0x7f]!;
  }

  function blend(
    a: readonly [number, number, number],
    b: readonly [number, number, number],
    t: number,
  ): string {
    const r = Math.round(a[0] + (b[0] - a[0]) * t);
    const g = Math.round(a[1] + (b[1] - a[1]) * t);
    const bl = Math.round(a[2] + (b[2] - a[2]) * t);
    return `rgb(${r}, ${g}, ${bl})`;
  }

  function rgbString(c: readonly [number, number, number]): string {
    return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
  }

  interface Led {
    cx: number;
    cy: number;
    color: string;
  }

  const leds = $derived.by<Led[]>(() => {
    const active = rgb(activeColor);
    const inactive = rgb(inactiveColor);
    const frac = Math.max(0, Math.min(1, value / 127));
    const activeLeds = Math.round(frac * (NUM_LEDS - 1));

    const out: Led[] = [];
    for (let i = 0; i < NUM_LEDS; i++) {
      const angleDeg = START_ANGLE - (i / (NUM_LEDS - 1)) * SWEEP;
      const angleRad = (angleDeg * Math.PI) / 180;
      const lx = CX + (RADIUS - 4) * Math.cos(angleRad);
      const ly = CY - (RADIUS - 4) * Math.sin(angleRad);

      let color: string;
      switch (displayType) {
        case DisplayType.BAR:
          color = i <= activeLeds ? rgbString(active) : rgbString(inactive);
          break;
        case DisplayType.DOT:
          color = i === activeLeds ? rgbString(active) : rgbString(inactive);
          break;
        case DisplayType.BLENDED_BAR:
          if (i <= activeLeds) {
            const t = activeLeds === 0 ? 1 : i / activeLeds;
            color = blend(inactive, active, t);
          } else {
            color = rgbString(inactive);
          }
          break;
        case DisplayType.BLENDED_DOT:
          {
            const dist = Math.abs(i - activeLeds);
            const t = Math.max(0, 1 - dist / 3);
            color = blend(inactive, active, t);
          }
          break;
        default:
          color = rgbString(inactive);
      }
      out.push({ cx: lx, cy: ly, color });
    }
    return out;
  });
</script>

<svg viewBox="0 0 100 100" class="indicator" aria-label="Indicator preview">
  <circle cx={CX} cy={CY} r={RADIUS} fill="#151518" stroke="#2a2a30" stroke-width="1" />
  {#each leds as led}
    <circle cx={led.cx} cy={led.cy} r="3.5" fill={led.color} />
  {/each}
</svg>

<style>
  .indicator {
    width: 96px;
    height: 96px;
    display: block;
  }
</style>
