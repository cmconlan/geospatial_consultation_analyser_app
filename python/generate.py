"""
Generate a synthetic planning-consultation dataset for Brighton & Hove.

The output schema mirrors what an LLM extraction stage would produce from raw consultation
responses: each response gets a stance, a sentiment score and one or more themes with a
confidence score. Here those fields are simulated rather than extracted.

Usage:
    python python/generate.py                 # uses data/raw/brighton_hove_boundary.geojson
    python python/generate.py --boundary path/to/boundary.geojson --seed 7

Writes to data/synthetic/:
    applications.csv      one row per planning application
    responses.csv         one row per consultation response
    response_themes.csv   one row per (response, theme): the "LLM output" layer
    themes.json           theme taxonomy (ids + labels)
    scenarios.json        ground truth: the planted patterns, for validating the app later
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point, shape
from shapely.ops import unary_union
from shapely.prepared import prep

import config as cfg
from text_templates import TEMPLATES

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOUNDARY = ROOT / "data" / "raw" / "brighton_hove_boundary.geojson"
OUT_DIR = ROOT / "data" / "synthetic"

M_PER_DEG_LAT = 111_320.0


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def load_boundary(path: Path):
    gj = json.loads(Path(path).read_text())
    geoms = [shape(f["geometry"]) for f in gj["features"]]
    return unary_union(geoms)


def weighted_choice(rng: np.random.Generator, weights: dict[str, float], size=None):
    keys = list(weights)
    p = np.array([weights[k] for k in keys], dtype=float)
    return rng.choice(keys, size=size, p=p / p.sum())


def month_weights(temporal: dict, months: pd.PeriodIndex) -> np.ndarray:
    """Relative likelihood of an application being submitted in each month."""
    idx = np.arange(len(months))
    moy = np.array([m.month for m in months])
    profile = temporal.get("profile", "flat")

    if profile == "flat":
        w = np.ones(len(months))
    elif profile == "seasonal":
        amp, peak = temporal.get("amplitude", 0.5), temporal.get("peak_month", 7)
        w = 1 + amp * np.cos(2 * np.pi * (moy - peak) / 12)
    elif profile == "emerging":
        start, growth = temporal["start_index"], temporal.get("growth", 0.2)
        w = np.where(idx < start, 0.0, 1 + growth * (idx - start))
    elif profile == "fading":
        peak, width = temporal["peak_index"], temporal.get("width", 4)
        w = np.exp(-((idx - peak) ** 2) / (2 * width**2)) + 0.03
    else:
        raise ValueError(f"Unknown temporal profile: {profile}")
    return np.clip(w, 0, None)


def sample_location(rng, scenario: cfg.Scenario, boundary_prepared, max_tries: int = 100):
    """Gaussian scatter around a centre (or a point along a corridor), kept inside the boundary."""
    for _ in range(max_tries):
        if scenario.corridor:
            line = LineString([(lon, lat) for lat, lon in scenario.corridor])
            p = line.interpolate(rng.uniform(0, line.length))
            lat0, lon0 = p.y, p.x
        else:
            lat0, lon0 = scenario.centres[rng.integers(len(scenario.centres))]

        dy, dx = rng.normal(0, scenario.spread_m, size=2)
        lat = lat0 + dy / M_PER_DEG_LAT
        lon = lon0 + dx / (M_PER_DEG_LAT * math.cos(math.radians(lat0)))
        if boundary_prepared.contains(Point(lon, lat)):
            return lat, lon
    return None


def sample_sentiment(rng, mixture: list[tuple[float, float, float]], offset: float) -> float:
    weights = np.array([m[0] for m in mixture])
    w, mu, sd = mixture[rng.choice(len(mixture), p=weights / weights.sum())]
    return float(np.clip(rng.normal(mu + offset, sd), -1, 1))


def stance_from_sentiment(s: float) -> str:
    if s < -0.15:
        return "object"
    if s > 0.15:
        return "support"
    return "comment"


def sample_themes(rng, scenario_weights: dict[str, float]) -> list[tuple[str, float, bool]]:
    """Primary theme from the scenario mix; 0–2 secondary themes from a blended mix."""
    primary = str(weighted_choice(rng, scenario_weights))
    themes = [(primary, round(float(np.clip(rng.beta(8, 2), 0.3, 0.99)), 2), True)]

    n_secondary = rng.choice([0, 1, 2], p=[0.45, 0.40, 0.15])
    blended = {t: scenario_weights.get(t, 0) + 0.5 * cfg.BACKGROUND_THEME_WEIGHTS.get(t, 0)
               for t in cfg.THEMES}
    for _ in range(n_secondary):
        candidates = {t: w for t, w in blended.items() if t not in {x[0] for x in themes} and w > 0}
        if not candidates:
            break
        t = str(weighted_choice(rng, candidates))
        themes.append((t, round(float(np.clip(rng.beta(4, 3), 0.3, 0.95)), 2), False))
    return themes


def negative_binomial(rng, mean: float, k: float) -> int:
    p = k / (k + mean)
    return int(rng.negative_binomial(k, p))


# --------------------------------------------------------------------------------------
# Main generation
# --------------------------------------------------------------------------------------
def generate(boundary_path: Path, seed: int):
    rng = np.random.default_rng(seed)
    boundary = load_boundary(boundary_path)
    boundary_prepared = prep(boundary)

    months = pd.period_range(cfg.START_MONTH, cfg.END_MONTH, freq="M")
    window_start = months[0].start_time
    window_end = months[-1].end_time.normalize()

    applications, responses, response_themes = [], [], []
    app_counter, resp_counter = 0, 0

    for sc in cfg.SCENARIOS:
        mw = month_weights(sc.temporal, months)
        month_idx = rng.choice(len(months), size=sc.n_apps, p=mw / mw.sum())
        respondent_types = sc.respondent_types or cfg.RESPONDENT_TYPES

        for mi in month_idx:
            loc = sample_location(rng, sc, boundary_prepared)
            if loc is None:
                continue
            lat, lon = loc
            month = months[mi]
            submitted = month.start_time + pd.Timedelta(days=int(rng.integers(0, month.days_in_month)))
            app_type = str(weighted_choice(rng, sc.app_types))

            app_counter += 1
            app_id = f"DEMO-{submitted.year}-{app_counter:05d}"
            applications.append({
                "application_id": app_id,
                "scenario": sc.name,
                "area_label": sc.area_label,
                "lat": round(lat, 6),
                "lon": round(lon, 6),
                "app_type": app_type,
                "description": cfg.APP_TYPE_DESCRIPTIONS[app_type],
                "submitted_date": submitted.date().isoformat(),
                "status": str(weighted_choice(rng, cfg.STATUSES)),
            })

            n_resp = negative_binomial(rng, sc.responses_mean, sc.responses_dispersion)
            for _ in range(n_resp):
                # Most responses land in the 21-day consultation window, with a tail of late ones
                received = submitted + pd.Timedelta(days=int(min(rng.exponential(9), 60)))
                if received > window_end or received < window_start:
                    continue

                themes = sample_themes(rng, sc.theme_weights)
                primary = themes[0][0]
                sentiment = sample_sentiment(rng, sc.sentiment, cfg.THEMES[primary]["sentiment_offset"])
                stance = stance_from_sentiment(sentiment)

                resp_counter += 1
                resp_id = f"R{resp_counter:07d}"
                responses.append({
                    "response_id": resp_id,
                    "application_id": app_id,
                    "received_date": received.date().isoformat(),
                    "respondent_type": str(weighted_choice(rng, respondent_types)),
                    "stance": stance,
                    "sentiment": round(sentiment, 3),
                    "text": str(rng.choice(TEMPLATES[primary][stance])),
                })
                for theme, conf, is_primary in themes:
                    response_themes.append({
                        "response_id": resp_id, "theme": theme,
                        "confidence": conf, "is_primary": is_primary,
                    })

    apps_df = pd.DataFrame(applications)
    resp_df = pd.DataFrame(responses)
    themes_df = pd.DataFrame(response_themes)
    return apps_df, resp_df, themes_df


def write_outputs(apps_df, resp_df, themes_df, seed: int):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    apps_df.to_csv(OUT_DIR / "applications.csv", index=False)
    resp_df.to_csv(OUT_DIR / "responses.csv", index=False)
    themes_df.to_csv(OUT_DIR / "response_themes.csv", index=False)

    (OUT_DIR / "themes.json").write_text(json.dumps(
        [{"id": k, "label": v["label"]} for k, v in cfg.THEMES.items()], indent=2))

    scenarios = []
    for sc in cfg.SCENARIOS:
        d = asdict(sc)
        scenarios.append({k: d[k] for k in
                          ("name", "area_label", "description", "temporal", "theme_weights")})
    (OUT_DIR / "scenarios.json").write_text(json.dumps(
        {"seed": seed, "start_month": cfg.START_MONTH, "end_month": cfg.END_MONTH,
         "scenarios": scenarios}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)
    parser.add_argument("--seed", type=int, default=cfg.SEED)
    args = parser.parse_args()

    if not args.boundary.exists():
        raise SystemExit(f"Boundary not found at {args.boundary}. Run python/fetch_boundary.py first.")

    apps_df, resp_df, themes_df = generate(args.boundary, args.seed)
    write_outputs(apps_df, resp_df, themes_df, args.seed)
    print(f"Applications: {len(apps_df):,}  Responses: {len(resp_df):,}  "
          f"Theme labels: {len(themes_df):,}  -> {OUT_DIR}")


if __name__ == "__main__":
    main()
