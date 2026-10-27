/**
 * Sentiment colour scale: raspberry (negative) through a cool chalk neutral to Channel teal
 * (positive). Cells with too few responses for a meaningful mean are drawn in shingle grey.
 */

type RGB = [number, number, number];
type RGBA = [number, number, number, number];

export const SENTIMENT_STOPS: { at: number; hex: string }[] = [
  { at: -1, hex: "#8E1F47" },
  { at: -0.5, hex: "#C9567A" },
  { at: 0, hex: "#DCE0DC" },
  { at: 0.5, hex: "#5FA6B4" },
  { at: 1, hex: "#145C6B" },
];

/** Mean sentiment is clamped to ±SATURATE so typical values use the full ramp. */
export const SATURATE = 0.7;
export const MIN_N_FOR_SENTIMENT = 5;
const LOW_N: RGBA = [150, 158, 158, 110];

function hexToRgb(hex: string): RGB {
  const v = parseInt(hex.slice(1), 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}

const STOPS = SENTIMENT_STOPS.map((s) => ({ at: s.at, rgb: hexToRgb(s.hex) }));

export function sentimentColour(mean: number, n: number, alpha = 235): RGBA {
  if (n < MIN_N_FOR_SENTIMENT) return LOW_N;
  const t = Math.max(-1, Math.min(1, mean / SATURATE));
  for (let i = 1; i < STOPS.length; i++) {
    const a = STOPS[i - 1];
    const b = STOPS[i];
    if (t <= b.at) {
      const f = (t - a.at) / (b.at - a.at);
      return [
        Math.round(a.rgb[0] + f * (b.rgb[0] - a.rgb[0])),
        Math.round(a.rgb[1] + f * (b.rgb[1] - a.rgb[1])),
        Math.round(a.rgb[2] + f * (b.rgb[2] - a.rgb[2])),
        alpha,
      ];
    }
  }
  return [...STOPS[STOPS.length - 1].rgb, alpha];
}

export const legendGradient = `linear-gradient(to right, ${SENTIMENT_STOPS.map(
  (s) => `${s.hex} ${((s.at + 1) / 2) * 100}%`,
).join(", ")})`;
