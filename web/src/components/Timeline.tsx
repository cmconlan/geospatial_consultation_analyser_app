import { formatInt, formatMonth } from "../data";

interface Props {
  months: string[];
  totals: number[]; // city-wide responses per month for the selected theme
  range: [number, number];
  onChange: (r: [number, number]) => void;
}

/**
 * Monthly histogram with a two-handled range control laid over it.
 * Bars inside the selected window are solid; those outside are faded.
 */
export function Timeline({ months, totals, range, onChange }: Props) {
  const [m0, m1] = range;
  const max = Math.max(...totals, 1);
  const inWindow = totals.slice(m0, m1 + 1).reduce((a, b) => a + b, 0);
  const last = months.length - 1;

  return (
    <section className="timeline" aria-label="Time window">
      <div className="timeline__summary">
        <strong>
          {formatMonth(months[m0])} to {formatMonth(months[m1])}
        </strong>
        <span>{formatInt(inWindow)} responses in this window</span>
      </div>

      <div className="timeline__track">
        <div className="timeline__bars" aria-hidden>
          {totals.map((v, i) => (
            <div
              key={months[i]}
              className={`timeline__bar${i >= m0 && i <= m1 ? " is-in" : ""}`}
              style={{ height: `${Math.max((v / max) * 100, v > 0 ? 3 : 0)}%` }}
              title={`${formatMonth(months[i])}: ${formatInt(v)}`}
            />
          ))}
        </div>
        <input
          type="range"
          min={0}
          max={last}
          value={m0}
          aria-label="Start month"
          aria-valuetext={formatMonth(months[m0])}
          onChange={(e) => onChange([Math.min(Number(e.target.value), m1), m1])}
        />
        <input
          type="range"
          min={0}
          max={last}
          value={m1}
          aria-label="End month"
          aria-valuetext={formatMonth(months[m1])}
          onChange={(e) => onChange([m0, Math.max(Number(e.target.value), m0)])}
        />
      </div>

      <div className="timeline__axis" aria-hidden>
        <span>{formatMonth(months[0])}</span>
        <span>{formatMonth(months[last])}</span>
      </div>
    </section>
  );
}
