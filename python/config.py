"""
Configuration for the synthetic planning consultation dataset.

Everything here is fictional. Locations are real Brighton & Hove neighbourhoods so the map
reads plausibly, but no application, response or controversy is taken from real records.

The scenarios below are the "planted stories" the app should be able to surface:
  - steady hotspots (heritage in Kemptown, HMOs along Lewes Road)
  - a seasonal pattern (night-time economy / noise in the Lanes, peaking in summer)
  - polarised schemes (tall buildings on Hove seafront and at the Marina)
  - a fading issue (a regeneration consultation around London Road that peaks early)
  - an emerging issue (construction disruption along Western Road from March 2026)
"""

from __future__ import annotations

from dataclasses import dataclass, field

SEED = 42

# 24 monthly periods, Nov 2024 – Oct 2026 inclusive
START_MONTH = "2024-11"
END_MONTH = "2026-10"

# --------------------------------------------------------------------------------------
# Theme taxonomy (mirrors the label set an LLM extraction step would be asked to use)
# --------------------------------------------------------------------------------------
THEMES: dict[str, dict] = {
    "traffic_parking":        {"label": "Traffic & parking",           "sentiment_offset": -0.05},
    "heritage_conservation":  {"label": "Heritage & conservation",     "sentiment_offset": -0.05},
    "height_massing":         {"label": "Height & massing",            "sentiment_offset": -0.10},
    "daylight_overlooking":   {"label": "Daylight & overlooking",      "sentiment_offset": -0.10},
    "noise_night_economy":    {"label": "Noise & night-time economy",  "sentiment_offset": -0.05},
    "hmo_student_housing":    {"label": "HMOs & student housing",      "sentiment_offset": -0.05},
    "affordable_housing":     {"label": "Affordable housing",          "sentiment_offset": 0.20},
    "trees_green_space":      {"label": "Trees & green space",         "sentiment_offset": -0.05},
    "construction_disruption": {"label": "Construction disruption",    "sentiment_offset": -0.15},
    "seafront_tourism":       {"label": "Seafront & tourism",          "sentiment_offset": 0.10},
}

# Theme mix for responses outside the hotspots (and used to pick secondary themes)
BACKGROUND_THEME_WEIGHTS = {
    "traffic_parking": 3, "daylight_overlooking": 3, "trees_green_space": 2.5,
    "construction_disruption": 2, "height_massing": 1.5, "heritage_conservation": 1,
    "noise_night_economy": 1, "affordable_housing": 1, "hmo_student_housing": 0.5,
    "seafront_tourism": 0.3,
}

RESPONDENT_TYPES = {
    "resident": 0.78, "local_business": 0.10, "community_group": 0.08, "statutory_consultee": 0.04,
}

APP_TYPE_DESCRIPTIONS = {
    "householder": "Single-storey rear extension and alterations",
    "basement": "Excavation of basement and lightwell to front",
    "change_of_use_hmo": "Change of use from dwelling (C3) to small HMO (C4)",
    "licensing_premises": "Extension of opening hours and outdoor seating area",
    "shopfront": "Replacement shopfront and illuminated signage",
    "listed_building": "Internal and external alterations to listed building",
    "major_residential": "Erection of mixed-use residential-led building",
    "tall_building": "Redevelopment to provide a tall residential building with ground-floor uses",
    "regeneration": "Estate regeneration including affordable homes and public realm",
    "utility_works": "Temporary works compound and highway works",
    "demolition": "Demolition of existing building and construction of replacement",
    "tree_works": "Felling of trees and replacement planting",
}

STATUSES = {"pending": 0.25, "approved": 0.55, "refused": 0.15, "withdrawn": 0.05}


# --------------------------------------------------------------------------------------
# Scenarios
# --------------------------------------------------------------------------------------
@dataclass
class Scenario:
    name: str
    area_label: str
    n_apps: int
    # location: either a list of point centres (lat, lon) or a polyline for corridors
    centres: list[tuple[float, float]] = field(default_factory=list)
    corridor: list[tuple[float, float]] | None = None  # (lat, lon) vertices
    spread_m: float = 300.0
    app_types: dict[str, float] = field(default_factory=dict)
    theme_weights: dict[str, float] = field(default_factory=dict)
    # mixture of (weight, mean, sd) on a -1..1 sentiment scale
    sentiment: list[tuple[float, float, float]] = field(default_factory=lambda: [(1.0, -0.2, 0.4)])
    responses_mean: float = 5.0
    responses_dispersion: float = 1.5  # negative binomial k; lower = more skewed
    temporal: dict = field(default_factory=lambda: {"profile": "flat"})
    respondent_types: dict[str, float] | None = None
    description: str = ""


SCENARIOS: list[Scenario] = [
    Scenario(
        name="background",
        area_label="Brighton & Hove (general)",
        n_apps=700,
        centres=[
            (50.8420, -0.2150),  # Portslade
            (50.8310, -0.1750),  # Hove central
            (50.8320, -0.1880),  # Aldrington
            (50.8450, -0.1480),  # Preston Park
            (50.8550, -0.1500),  # Withdean
            (50.8650, -0.1500),  # Patcham
            (50.8550, -0.1250),  # Hollingbury
            (50.8290, -0.1260),  # Hanover
            (50.8260, -0.1030),  # Whitehawk
            (50.8370, -0.0780),  # Woodingdean
            (50.8070, -0.0580),  # Rottingdean
            (50.8040, -0.0400),  # Saltdean
            (50.8520, -0.1680),  # Westdene
        ],
        spread_m=550,
        app_types={"householder": 6, "basement": 0.5, "tree_works": 1, "demolition": 1,
                   "shopfront": 1, "major_residential": 0.5},
        theme_weights=BACKGROUND_THEME_WEIGHTS,
        sentiment=[(1.0, -0.25, 0.45)],
        responses_mean=3.0,
        temporal={"profile": "seasonal", "amplitude": 0.15, "peak_month": 6},
        description="Diffuse everyday casework across residential neighbourhoods.",
    ),
    Scenario(
        name="lanes_night_economy",
        area_label="North Laine & The Lanes",
        n_apps=140,
        centres=[(50.8250, -0.1395), (50.8222, -0.1405)],
        spread_m=220,
        app_types={"licensing_premises": 5, "shopfront": 2, "listed_building": 2, "householder": 1},
        theme_weights={"noise_night_economy": 6, "heritage_conservation": 4, "traffic_parking": 1},
        sentiment=[(0.8, -0.35, 0.35), (0.2, 0.40, 0.30)],
        responses_mean=12,
        temporal={"profile": "seasonal", "amplitude": 0.9, "peak_month": 7},
        respondent_types={"resident": 0.6, "local_business": 0.3, "community_group": 0.08,
                          "statutory_consultee": 0.02},
        description="Seasonal: licensing and noise objections peak each summer.",
    ),
    Scenario(
        name="kemptown_heritage",
        area_label="Kemptown & East Cliff",
        n_apps=90,
        centres=[(50.8190, -0.1260)],
        spread_m=320,
        app_types={"listed_building": 5, "basement": 2, "householder": 2},
        theme_weights={"heritage_conservation": 7, "daylight_overlooking": 2, "construction_disruption": 1},
        sentiment=[(1.0, -0.45, 0.30)],
        responses_mean=10,
        temporal={"profile": "flat"},
        description="Steady: persistent, mostly negative heritage objections.",
    ),
    Scenario(
        name="lewes_road_hmo",
        area_label="Lewes Road & Moulsecoomb",
        n_apps=160,
        centres=[(50.8370, -0.1250), (50.8460, -0.1150)],
        spread_m=420,
        app_types={"change_of_use_hmo": 7, "householder": 2},
        theme_weights={"hmo_student_housing": 7, "traffic_parking": 2, "noise_night_economy": 2},
        sentiment=[(1.0, -0.30, 0.35)],
        responses_mean=7,
        temporal={"profile": "flat"},
        description="Steady: HMO conversions drawing moderate objections.",
    ),
    Scenario(
        name="hove_seafront_tall",
        area_label="Hove seafront",
        n_apps=10,
        centres=[(50.8262, -0.1680)],
        spread_m=250,
        app_types={"tall_building": 1},
        theme_weights={"height_massing": 6, "daylight_overlooking": 3, "seafront_tourism": 2,
                       "affordable_housing": 1},
        sentiment=[(0.6, -0.55, 0.25), (0.4, 0.50, 0.25)],
        responses_mean=120,
        responses_dispersion=3,
        temporal={"profile": "flat"},
        description="Polarised: a few tall-building schemes with very high response volumes.",
    ),
    Scenario(
        name="marina_tall",
        area_label="Brighton Marina",
        n_apps=6,
        centres=[(50.8125, -0.1020)],
        spread_m=200,
        app_types={"tall_building": 1},
        theme_weights={"height_massing": 5, "traffic_parking": 3, "seafront_tourism": 2},
        sentiment=[(0.55, -0.50, 0.25), (0.45, 0.45, 0.25)],
        responses_mean=140,
        responses_dispersion=3,
        temporal={"profile": "flat"},
        description="Polarised: large schemes with split opinion.",
    ),
    Scenario(
        name="london_road_regen",
        area_label="London Road & Preston Road",
        n_apps=25,
        centres=[(50.8330, -0.1380)],
        spread_m=300,
        app_types={"regeneration": 3, "major_residential": 2},
        theme_weights={"affordable_housing": 6, "height_massing": 2, "trees_green_space": 1},
        sentiment=[(0.35, -0.30, 0.30), (0.65, 0.45, 0.30)],
        responses_mean=35,
        responses_dispersion=2,
        temporal={"profile": "fading", "peak_index": 3, "width": 4},
        description="Fading: a mostly supportive regeneration consultation peaking early on.",
    ),
    Scenario(
        name="western_road_baseline",
        area_label="Western Road",
        n_apps=80,
        corridor=[(50.8247, -0.1430), (50.8243, -0.1520), (50.8253, -0.1600), (50.8262, -0.1660)],
        spread_m=60,
        app_types={"shopfront": 4, "householder": 2, "licensing_premises": 1},
        theme_weights={"traffic_parking": 3, "noise_night_economy": 1, "heritage_conservation": 1},
        sentiment=[(1.0, -0.10, 0.40)],
        responses_mean=6,
        temporal={"profile": "flat"},
        description="Ordinary high-street casework along Western Road.",
    ),
    Scenario(
        name="western_road_works",
        area_label="Western Road",
        n_apps=35,
        corridor=[(50.8247, -0.1430), (50.8243, -0.1520), (50.8253, -0.1600), (50.8262, -0.1660)],
        spread_m=60,
        app_types={"utility_works": 3, "demolition": 2, "major_residential": 1},
        theme_weights={"construction_disruption": 7, "traffic_parking": 4, "noise_night_economy": 1},
        sentiment=[(1.0, -0.60, 0.25)],
        responses_mean=30,
        responses_dispersion=2,
        temporal={"profile": "emerging", "start_index": 16, "growth": 0.25},
        description="EMERGING: construction disruption along Western Road from March 2026.",
    ),
]
