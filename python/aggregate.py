"""
Aggregate the synthetic responses onto H3 hexagons and export compact JSON for the web app.

Design: we export *monthly building blocks* per (cell, theme, month) – a response count, a
sentiment sum and stance counts. The browser sums these over whatever time window the user
selects and derives mean sentiment and change scores itself, so no server is needed.

A response counts towards every theme it is labelled with (confidence >= MIN_CONFIDENCE),
and once towards the special theme "all".

Usage:
    python python/aggregate.py
Reads:
    data/raw/brighton_hove_boundary.geojson, data/synthetic/*.csv
Writes to web/public/data/:
    aggregates_r8.json, aggregates_r9.json   columnar monthly aggregates + the cell list
    applications.json                         per-application details for the drill-down panel
    themes.json, boundary.geojson, meta.json
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

import config as cfg

ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "data" / "synthetic"
BOUNDARY = ROOT / "data" / "raw" / "brighton_hove_boundary.geojson"
OUT = ROOT / "web" / "public" / "data"

RESOLUTIONS = [8, 9]
MIN_CONFIDENCE = 0.5  # ignore weak secondary theme labels, as you would with real LLM output
SNIPPETS_PER_APP = 3


def load_inputs():
    apps = pd.read_csv(SYN / "applications.csv")
    resp = pd.read_csv(SYN / "responses.csv")
    labels = pd.read_csv(SYN / "response_themes.csv")
    boundary = unary_union([shape(f["geometry"]) for f in json.loads(BOUNDARY.read_text())["features"]])
    return apps, resp, labels, boundary


def grid_cells(boundary, res: int) -> set[str]:
    """All H3 cells whose centre lies inside the boundary."""
    return set(h3.geo_to_cells(mapping(boundary), res))


def build_aggregates(apps, resp, labels, boundary, res: int, months: list[str], theme_ids: list[str]):
    cell_col = f"h3_r{res}"
    df = resp.merge(apps[["application_id", cell_col]], on="application_id")
    df["month"] = df["received_date"].str[:7]

    kept = labels[labels["confidence"] >= MIN_CONFIDENCE][["response_id", "theme"]]
    themed = df.merge(kept, on="response_id")
    everything = df.assign(theme="all")
    long = pd.concat([everything, themed], ignore_index=True)

    agg = (long.groupby([cell_col, "theme", "month"])
           .agg(n=("response_id", "size"),
                sentiment_sum=("sentiment", "sum"),
                n_object=("stance", lambda s: int((s == "object").sum())),
                n_support=("stance", lambda s: int((s == "support").sum())))
           .reset_index())

    # Cell list: every hex in the boundary, plus any coastal hex that holds data
    cells = sorted(grid_cells(boundary, res) | set(agg[cell_col]))
    cell_idx = {c: i for i, c in enumerate(cells)}
    theme_idx = {t: i for i, t in enumerate(theme_ids)}
    month_idx = {m: i for i, m in enumerate(months)}

    agg["cell_i"] = agg[cell_col].map(cell_idx).astype(int)
    agg["theme_i"] = agg["theme"].map(theme_idx).astype(int)
    agg["month_i"] = agg["month"].map(month_idx).astype(int)
    agg = agg.sort_values(["theme_i", "cell_i", "month_i"])

    return {
        "resolution": res,
        "months": months,
        "themes": theme_ids,
        "cells": cells,
        "rows": {
            "cell": agg["cell_i"].tolist(),
            "theme": agg["theme_i"].tolist(),
            "month": agg["month_i"].tolist(),
            "n": agg["n"].astype(int).tolist(),
            "sentiment_sum": agg["sentiment_sum"].round(3).tolist(),
            "n_object": agg["n_object"].astype(int).tolist(),
            "n_support": agg["n_support"].astype(int).tolist(),
        },
    }


def build_applications(apps, resp, labels, rng):
    kept = labels[labels["confidence"] >= MIN_CONFIDENCE].merge(
        resp[["response_id", "application_id"]], on="response_id")
    theme_counts = (kept.groupby(["application_id", "theme"]).size()
                    .rename("n").reset_index()
                    .sort_values(["application_id", "n"], ascending=[True, False]))
    top_themes = theme_counts.groupby("application_id").apply(
        lambda g: [{"theme": t, "n": int(n)} for t, n in zip(g["theme"].head(3), g["n"].head(3))],
        include_groups=False)

    stats = resp.groupby("application_id").agg(
        n_responses=("response_id", "size"),
        mean_sentiment=("sentiment", "mean"),
        n_object=("stance", lambda s: int((s == "object").sum())),
        n_support=("stance", lambda s: int((s == "support").sum())),
    )

    out = []
    for app in apps.itertuples(index=False):
        aid = app.application_id
        app_resp = resp[resp["application_id"] == aid]
        snippets = []
        if len(app_resp):
            sample = app_resp.sample(min(SNIPPETS_PER_APP, len(app_resp)), random_state=rng.integers(1e9))
            snippets = [{"stance": r.stance, "text": r.text} for r in sample.itertuples()]
        s = stats.loc[aid] if aid in stats.index else None
        out.append({
            "id": aid,
            "lat": app.lat, "lon": app.lon,
            "h3_r8": app.h3_r8, "h3_r9": app.h3_r9,
            "area": app.area_label,
            "type": app.app_type,
            "description": app.description,
            "submitted": app.submitted_date,
            "status": app.status,
            "n_responses": int(s.n_responses) if s is not None else 0,
            "mean_sentiment": round(float(s.mean_sentiment), 3) if s is not None else None,
            "n_object": int(s.n_object) if s is not None else 0,
            "n_support": int(s.n_support) if s is not None else 0,
            "top_themes": top_themes.get(aid, []),
            "snippets": snippets,
        })
    return out


def write_json(path: Path, obj, compact=True):
    path.write_text(json.dumps(obj, separators=(",", ":")) if compact else json.dumps(obj, indent=2))
    return path.stat().st_size / 1024


def main():
    apps, resp, labels, boundary = load_inputs()
    rng = np.random.default_rng(cfg.SEED)
    OUT.mkdir(parents=True, exist_ok=True)

    for res in RESOLUTIONS:
        apps[f"h3_r{res}"] = [h3.latlng_to_cell(lat, lon, res) for lat, lon in zip(apps["lat"], apps["lon"])]

    months = [str(p) for p in pd.period_range(cfg.START_MONTH, cfg.END_MONTH, freq="M")]
    theme_ids = ["all"] + list(cfg.THEMES)

    sizes = {}
    for res in RESOLUTIONS:
        agg = build_aggregates(apps, resp, labels, boundary, res, months, theme_ids)
        total_all = sum(n for n, t in zip(agg["rows"]["n"], agg["rows"]["theme"]) if t == 0)
        assert total_all == len(resp), f"r{res}: 'all' total {total_all} != responses {len(resp)}"
        sizes[f"aggregates_r{res}.json"] = write_json(OUT / f"aggregates_r{res}.json", agg)
        print(f"r{res}: {len(agg['cells']):,} cells, {len(agg['rows']['n']):,} rows")

    sizes["applications.json"] = write_json(OUT / "applications.json", build_applications(apps, resp, labels, rng))
    sizes["themes.json"] = write_json(OUT / "themes.json", [{"id": "all", "label": "All themes"}] +
                                      [{"id": k, "label": v["label"]} for k, v in cfg.THEMES.items()],
                                      compact=False)
    sizes["boundary.geojson"] = write_json(OUT / "boundary.geojson", {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {"name": "Brighton and Hove"},
                      "geometry": mapping(boundary)}]})
    sizes["meta.json"] = write_json(OUT / "meta.json", {
        "generated": date.today().isoformat(),
        "seed": cfg.SEED,
        "months": months,
        "resolutions": RESOLUTIONS,
        "min_confidence": MIN_CONFIDENCE,
        "n_applications": int(len(apps)),
        "n_responses": int(len(resp)),
        "synthetic": True,
        "attribution": ("Boundary: Office for National Statistics, OGL v3.0. "
                        "Contains OS data © Crown copyright and database right 2024."),
    }, compact=False)

    print("\nWrote to", OUT)
    for name, kb in sizes.items():
        print(f"  {name:<22} {kb:>8.0f} KB")


if __name__ == "__main__":
    main()
