export interface AggregateFile {
  resolution: number;
  months: string[];
  themes: string[];
  cells: string[];
  rows: {
    cell: number[];
    theme: number[];
    month: number[];
    n: number[];
    sentiment_sum: number[];
    n_object: number[];
    n_support: number[];
  };
}

export interface Theme {
  id: string;
  label: string;
}

export interface Meta {
  generated: string;
  months: string[];
  resolutions: number[];
  n_applications: number;
  n_responses: number;
  attribution: string;
}

/** Totals for one hex over the selected window. */
export interface CellStat {
  hex: string;
  n: number;
  sentimentSum: number;
  nObject: number;
  nSupport: number;
  mean: number;
}

export type Resolution = 8 | 9;
export type ViewMode = "3d" | "flat";
