import type { AggregateFile, CellStat } from "./types";

const BASE = import.meta.env.BASE_URL;

export async function loadJSON<T>(file: string): Promise<T> {
  const res = await fetch(`${BASE}data/${file}`);
  if (!res.ok) {
    throw new Error(`Couldn't load data/${file} (HTTP ${res.status}). Run python/aggregate.py to create it.`);
  }
  return res.json() as Promise<T>;
}

/**
 * Sum the monthly building blocks for one theme over months [m0, m1] (inclusive),
 * returning one record per hex that has any responses.
 */
export function windowStats(agg: AggregateFile, themeIdx: number, m0: number, m1: number): CellStat[] {
  const { cell, theme, month, n, sentiment_sum, n_object, n_support } = agg.rows;
  const byCell = new Map<number, CellStat>();

  for (let i = 0; i < n.length; i++) {
    if (theme[i] !== themeIdx || month[i] < m0 || month[i] > m1) continue;
    let s = byCell.get(cell[i]);
    if (!s) {
      s = { hex: agg.cells[cell[i]], n: 0, sentimentSum: 0, nObject: 0, nSupport: 0, mean: 0 };
      byCell.set(cell[i], s);
    }
    s.n += n[i];
    s.sentimentSum += sentiment_sum[i];
    s.nObject += n_object[i];
    s.nSupport += n_support[i];
  }

  const out = [...byCell.values()];
  for (const s of out) s.mean = s.sentimentSum / s.n;
  return out;
}

/** City-wide responses per month for one theme (drives the timeline histogram). */
export function monthlyTotals(agg: AggregateFile, themeIdx: number): number[] {
  const totals = new Array(agg.months.length).fill(0);
  const { theme, month, n } = agg.rows;
  for (let i = 0; i < n.length; i++) {
    if (theme[i] === themeIdx) totals[month[i]] += n[i];
  }
  return totals;
}

/** Responses per theme within the window (shown beside each theme in the list). */
export function themeTotals(agg: AggregateFile, m0: number, m1: number): number[] {
  const totals = new Array(agg.themes.length).fill(0);
  const { theme, month, n } = agg.rows;
  for (let i = 0; i < n.length; i++) {
    if (month[i] >= m0 && month[i] <= m1) totals[theme[i]] += n[i];
  }
  return totals;
}

const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatMonth(ym: string): string {
  const [y, m] = ym.split("-");
  return `${MONTH_NAMES[Number(m) - 1]} ${y}`;
}

export const formatInt = (x: number) => x.toLocaleString("en-GB");

export function formatSentiment(x: number): string {
  const v = x.toFixed(2);
  return x > 0 ? `+${v}` : v.replace("-", "−");
}
