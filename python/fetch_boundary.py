"""
Download the Brighton and Hove local authority boundary from the ONS Open Geography Portal.

Source: Local Authority Districts (December 2023) Boundaries UK BGC
        (generalised to 20 m, clipped to the coastline at Mean High Water).
Licence: Open Government Licence v3.0.
Attribution: Source: Office for National Statistics licensed under the Open Government
             Licence v.3.0. Contains OS data © Crown copyright and database right 2024.

Usage:
    python python/fetch_boundary.py
Writes:
    data/raw/brighton_hove_boundary.geojson  (WGS84 / EPSG:4326)
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

LAD_CODE = "E06000043"  # Brighton and Hove
SERVICE = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Local_Authority_Districts_December_2023_Boundaries_UK_BGC/FeatureServer/0/query"
)
OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "brighton_hove_boundary.geojson"


def fetch_boundary() -> dict:
    params = {
        "where": f"LAD23CD='{LAD_CODE}'",
        "outFields": "LAD23CD,LAD23NM",
        "outSR": "4326",
        "f": "geojson",
    }
    resp = requests.get(SERVICE, params=params, timeout=60)
    resp.raise_for_status()
    gj = resp.json()

    if "error" in gj:
        raise RuntimeError(f"ArcGIS service returned an error: {gj['error']}")
    features = gj.get("features", [])
    if len(features) != 1:
        raise RuntimeError(f"Expected 1 feature for {LAD_CODE}, got {len(features)}")

    props = features[0]["properties"]
    print(f"Fetched {props.get('LAD23NM')} ({props.get('LAD23CD')}), "
          f"geometry type: {features[0]['geometry']['type']}")
    return gj


def main() -> None:
    gj = fetch_boundary()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(gj))
    print(f"Saved to {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
