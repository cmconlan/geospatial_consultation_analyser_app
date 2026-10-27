"""
Preview the exported H3 aggregates as flat hex maps: response volume and mean sentiment for one
theme over one time window. This is a 2D stand-in for what the web app will draw in 3D.

Usage:
    python python/check_aggregates.py
    python python/check_aggregates.py --theme construction_disruption --res 9 --start 2026-03 --end 2026-10
Writes:
    data/synthetic/checks/hexes_<theme>_r<res>.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import h3
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize, TwoSlopeNorm

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "web" / "public" / "data"
OUT = ROOT / "data" / "synthetic" / "checks"
MIN_N_FOR_SENTIMENT = 5  # cells with fewer responses are drawn faded on the sentiment map


def load(res: int):
    agg = json.loads((DATA / f"aggregates_r{res}.json").read_text())
    rows = pd.DataFrame(agg["rows"])
    return agg, rows


def window_totals(agg, rows, theme: str, start: str, end: str) -> pd.DataFrame:
    t = agg["themes"].index(theme)
    m0, m1 = agg["months"].index(start), agg["months"].index(end)
    sel = rows[(rows["theme"] == t) & rows["month"].between(m0, m1)]
    out = sel.groupby("cell")[["n", "sentiment_sum", "n_object", "n_support"]].sum()
    out["mean_sentiment"] = out["sentiment_sum"] / out["n"]
    return out


def hex_polys(cells: list[str]):
    return [[(lng, lat) for lat, lng in h3.cell_to_boundary(c)] for c in cells]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--theme", default="all")
    p.add_argument("--res", type=int, default=8)
    p.add_argument("--start", default=None)
    p.add_argument("--end", default=None)
    a = p.parse_args()

    agg, rows = load(a.res)
    start, end = a.start or agg["months"][0], a.end or agg["months"][-1]
    totals = window_totals(agg, rows, a.theme, start, end)

    cells = agg["cells"]
    all_polys = hex_polys(cells)
    data_cells = [cells[i] for i in totals.index]
    data_polys = hex_polys(data_cells)
    boundary = json.loads((DATA / "boundary.geojson").read_text())["features"][0]["geometry"]

    fig, axes = plt.subplots(1, 2, figsize=(15, 6.5))
    for ax in axes:
        ax.add_collection(PolyCollection(all_polys, facecolor="none", edgecolor="#e2e2e2", lw=0.3))
        polys = boundary["coordinates"] if boundary["type"] == "MultiPolygon" else [boundary["coordinates"]]
        for poly in polys:
            x, y = zip(*poly[0])
            ax.plot(x, y, color="#666", lw=0.8)
        ax.set_aspect(1 / 0.63)
        ax.autoscale_view()
        ax.set_xticks([]); ax.set_yticks([])

    # Volume
    vol = totals["n"].values
    pc = PolyCollection(data_polys, array=vol, cmap="viridis",
                        norm=Normalize(0, np.percentile(vol, 98)), edgecolor="white", lw=0.2)
    axes[0].add_collection(pc)
    fig.colorbar(pc, ax=axes[0], shrink=0.7, label="Responses")
    axes[0].set_title(f"Volume · {a.theme} · {start} to {end} · r{a.res}")

    # Sentiment (faded where n is small)
    sent = totals["mean_sentiment"].clip(-1, 1).values
    alpha = np.where(totals["n"].values >= MIN_N_FOR_SENTIMENT, 1.0, 0.25)
    pc2 = PolyCollection(data_polys, array=sent, cmap="RdBu", norm=TwoSlopeNorm(0, -0.8, 0.8),
                         edgecolor="white", lw=0.2, alpha=alpha)
    axes[1].add_collection(pc2)
    fig.colorbar(pc2, ax=axes[1], shrink=0.7, label="Mean sentiment (−1 to 1)")
    axes[1].set_title(f"Sentiment (faded if n < {MIN_N_FOR_SENTIMENT})")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"hexes_{a.theme}_r{a.res}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=130)

    top = totals.sort_values("n", ascending=False).head(5).copy()
    top.index = [cells[i] for i in top.index]
    print(f"Top cells for '{a.theme}' ({start} to {end}, r{a.res}):")
    print(top[["n", "mean_sentiment", "n_object", "n_support"]].round(2).to_string())
    print(f"\nCells with data: {len(totals):,} of {len(cells):,}.  Saved {path}")


if __name__ == "__main__":
    main()
