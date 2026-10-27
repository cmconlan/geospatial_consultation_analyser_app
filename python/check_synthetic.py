"""
Sanity checks for the synthetic dataset: prints summary tables and saves a diagnostic figure
showing where applications fall and whether the planted temporal patterns came through.

Usage:
    python python/check_synthetic.py
Writes:
    data/synthetic/checks/overview.png
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SYN = ROOT / "data" / "synthetic"
BOUNDARY = ROOT / "data" / "raw" / "brighton_hove_boundary.geojson"


def main():
    apps = pd.read_csv(SYN / "applications.csv")
    resp = pd.read_csv(SYN / "responses.csv", parse_dates=["received_date"])
    themes = pd.read_csv(SYN / "response_themes.csv")
    labels = {t["id"]: t["label"] for t in json.loads((SYN / "themes.json").read_text())}

    df = resp.merge(apps[["application_id", "scenario", "lat", "lon"]], on="application_id")
    df["month"] = df["received_date"].dt.to_period("M")

    # ---- Summary tables ---------------------------------------------------------------
    print("\nApplications and responses by scenario")
    summary = df.groupby("scenario").agg(
        responses=("response_id", "size"), mean_sentiment=("sentiment", "mean"),
        pct_object=("stance", lambda s: (s == "object").mean() * 100))
    summary.insert(0, "applications", apps.groupby("scenario").size())
    print(summary.round(2).sort_values("responses", ascending=False).to_string())

    print("\nResponses by primary theme")
    prim = themes[themes["is_primary"]].merge(resp[["response_id", "sentiment"]], on="response_id")
    print(prim.groupby("theme").agg(n=("response_id", "size"), mean_sentiment=("sentiment", "mean"))
          .round(2).sort_values("n", ascending=False).to_string())

    print(f"\nThemes per response: {themes.groupby('response_id').size().mean():.2f} on average")
    print(f"Stance split: {resp['stance'].value_counts(normalize=True).round(3).to_dict()}")

    # ---- Figure -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={"width_ratios": [1.3, 1]})

    ax = axes[0]
    boundary = unary_union([shape(f["geometry"]) for f in json.loads(BOUNDARY.read_text())["features"]])
    for poly in getattr(boundary, "geoms", [boundary]):
        x, y = poly.exterior.xy
        ax.plot(x, y, color="#555", lw=0.8)
    palette = [c for i, c in enumerate(plt.get_cmap("tab10").colors) if i != 7]  # skip grey
    hotspots = [s for s in apps["scenario"].unique() if s != "background"]
    colours = {s: palette[i % len(palette)] for i, s in enumerate(sorted(hotspots))}
    colours["background"] = "#bbbbbb"
    for name, g in apps.groupby("scenario"):
        ax.scatter(g["lon"], g["lat"], s=6 if name == "background" else 10,
                   alpha=0.35 if name == "background" else 0.8, label=name, color=colours[name])
    ax.set_aspect(1 / 0.63)  # approximate for latitude ~50.8
    ax.set_title("Synthetic applications by scenario")
    ax.legend(fontsize=7, markerscale=2, loc="upper right")

    ax = axes[1]
    with_theme = df.merge(themes, on="response_id")
    checks = [
        ("western_road_works", "construction_disruption", "Western Road: construction (emerging)"),
        ("lanes_night_economy", "noise_night_economy", "Lanes: noise & night economy (seasonal)"),
        ("london_road_regen", "affordable_housing", "London Road: affordable housing (fading)"),
        ("kemptown_heritage", "heritage_conservation", "Kemptown: heritage (steady)"),
    ]
    all_months = pd.period_range(df["month"].min(), df["month"].max(), freq="M")
    for scenario, theme, label in checks:
        s = (with_theme[(with_theme["scenario"] == scenario) & (with_theme["theme"] == theme)]
             .groupby("month").size().reindex(all_months, fill_value=0))
        ax.plot(s.index.to_timestamp(), s.values, label=label, lw=1.6)
    ax.set_title("Monthly responses for planted patterns")
    ax.set_ylabel("Responses")
    ax.legend(fontsize=8)
    fig.autofmt_xdate()

    out = SYN / "checks"
    out.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(out / "overview.png", dpi=130)
    print(f"\nSaved figure to {out / 'overview.png'}")
    print(f"Theme labels available: {', '.join(labels.values())}")


if __name__ == "__main__":
    main()
