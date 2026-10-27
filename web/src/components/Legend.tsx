import { legendGradient, MIN_N_FOR_SENTIMENT, SATURATE } from "../colour";
import type { ViewMode } from "../types";

export function Legend({ mode }: { mode: ViewMode }) {
  return (
    <aside className="legend" aria-label="Map key">
      <p className="legend__title">Mean sentiment of responses</p>
      <div className="legend__ramp" style={{ background: legendGradient }} />
      <div className="legend__ends">
        <span>Negative</span>
        <span>Neutral</span>
        <span>Positive</span>
      </div>
      <p className="legend__note">Scale saturates at ±{SATURATE}.</p>
      <p className="legend__lowN">
        <span className="legend__swatch" aria-hidden /> Fewer than {MIN_N_FOR_SENTIMENT} responses
      </p>
      <p className="legend__note">
        {mode === "3d"
          ? "Height shows response volume (square-root scale)."
          : "Switch to 3D to see response volume as height."}
      </p>
    </aside>
  );
}
