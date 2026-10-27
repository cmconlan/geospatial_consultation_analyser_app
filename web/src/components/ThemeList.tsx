import type { Theme } from "../types";
import { formatInt } from "../data";

interface Props {
  themes: Theme[];
  totals: number[]; // aligned with themes
  selected: string;
  onSelect: (id: string) => void;
}

export function ThemeList({ themes, totals, selected, onSelect }: Props) {
  const max = Math.max(...totals.slice(1), 1); // scale bars against the largest single theme
  return (
    <fieldset className="theme-list">
      <legend>Theme</legend>
      {themes.map((t, i) => {
        const isAll = t.id === "all";
        return (
          <button
            key={t.id}
            type="button"
            className={`theme-row${isAll ? " theme-row--all" : ""}`}
            aria-pressed={selected === t.id}
            onClick={() => onSelect(t.id)}
          >
            <span className="theme-row__label">{t.label}</span>
            <span className="theme-row__count">{formatInt(totals[i])}</span>
            {!isAll && (
              <span className="theme-row__bar" style={{ width: `${(totals[i] / max) * 100}%` }} aria-hidden />
            )}
          </button>
        );
      })}
    </fieldset>
  );
}
