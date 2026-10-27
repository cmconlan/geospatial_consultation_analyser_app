import type { CellStat } from "../types";
import { formatInt, formatSentiment } from "../data";
import { MIN_N_FOR_SENTIMENT } from "../colour";

interface Props {
  cell: CellStat;
  x: number;
  y: number;
  themeLabel: string;
}

export function HoverCard({ cell, x, y, themeLabel }: Props) {
  const pct = (k: number) => `${Math.round((k / cell.n) * 100)}%`;
  return (
    <div className="hovercard" style={{ left: x + 14, top: y + 14 }} role="status">
      <p className="hovercard__n">
        <strong>{formatInt(cell.n)}</strong> {cell.n === 1 ? "response" : "responses"}
      </p>
      <p className="hovercard__theme">{themeLabel}</p>
      {cell.n >= MIN_N_FOR_SENTIMENT ? (
        <dl>
          <dt>Mean sentiment</dt>
          <dd>{formatSentiment(cell.mean)}</dd>
          <dt>Objecting</dt>
          <dd>{pct(cell.nObject)}</dd>
          <dt>Supporting</dt>
          <dd>{pct(cell.nSupport)}</dd>
        </dl>
      ) : (
        <p className="hovercard__thin">Too few responses to summarise sentiment.</p>
      )}
    </div>
  );
}
