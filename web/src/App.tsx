import { useEffect, useMemo, useState } from "react";
import DeckGL from "@deck.gl/react";
import { LinearInterpolator, type MapViewState, type PickingInfo } from "@deck.gl/core";
import { GeoJsonLayer } from "@deck.gl/layers";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import { Map } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";

import type { AggregateFile, CellStat, Meta, Resolution, Theme, ViewMode } from "./types";
import { loadJSON, monthlyTotals, themeTotals, windowStats } from "./data";
import { sentimentColour } from "./colour";
import { ThemeList } from "./components/ThemeList";
import { Segmented } from "./components/Segmented";
import { Timeline } from "./components/Timeline";
import { Legend } from "./components/Legend";
import { HoverCard } from "./components/HoverCard";

const MAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const PITCH_3D = 52;
// Height (metres) of the tallest column at each resolution
const MAX_HEIGHT: Record<Resolution, number> = { 8: 2600, 9: 1500 };

const INITIAL_VIEW: MapViewState = {
  longitude: -0.142,
  latitude: 50.818,
  zoom: 11.7,
  pitch: PITCH_3D,
  bearing: -12,
};

interface Loaded {
  meta: Meta;
  themes: Theme[];
  agg: Record<Resolution, AggregateFile>;
  boundary: GeoJSON.FeatureCollection;
}

const prefersReducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export default function App() {
  const [data, setData] = useState<Loaded | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [themeId, setThemeId] = useState("all");
  const [res, setRes] = useState<Resolution>(8);
  const [mode, setMode] = useState<ViewMode>("3d");
  const [range, setRange] = useState<[number, number]>([0, 0]);
  const [viewState, setViewState] = useState<MapViewState>(INITIAL_VIEW);
  const [hover, setHover] = useState<{ cell: CellStat; x: number; y: number } | null>(null);

  useEffect(() => {
    Promise.all([
      loadJSON<Meta>("meta.json"),
      loadJSON<Theme[]>("themes.json"),
      loadJSON<AggregateFile>("aggregates_r8.json"),
      loadJSON<AggregateFile>("aggregates_r9.json"),
      loadJSON<GeoJSON.FeatureCollection>("boundary.geojson"),
    ])
      .then(([meta, themes, a8, a9, boundary]) => {
        setData({ meta, themes, agg: { 8: a8, 9: a9 }, boundary });
        setRange([0, meta.months.length - 1]);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const agg = data?.agg[res];
  const themeIdx = agg ? agg.themes.indexOf(themeId) : -1;

  const cells = useMemo(
    () => (agg ? windowStats(agg, themeIdx, range[0], range[1]) : []),
    [agg, themeIdx, range],
  );
  const monthTotals = useMemo(() => (agg ? monthlyTotals(agg, themeIdx) : []), [agg, themeIdx]);
  const totalsByTheme = useMemo(
    () => (data ? themeTotals(data.agg[8], range[0], range[1]) : []),
    [data, range],
  );

  const maxSqrt = Math.sqrt(Math.max(1, ...cells.map((c) => c.n)));

  function changeMode(next: ViewMode) {
    setMode(next);
    setViewState((v) => ({
      ...v,
      pitch: next === "3d" ? PITCH_3D : 0,
      bearing: next === "3d" ? INITIAL_VIEW.bearing : 0,
      transitionDuration: prefersReducedMotion() ? 0 : 700,
      transitionInterpolator: new LinearInterpolator(["pitch", "bearing"]),
    }));
  }

  const layers = data
    ? [
        new GeoJsonLayer({
          id: "boundary",
          data: data.boundary,
          stroked: true,
          filled: false,
          getLineColor: [34, 52, 60, 160],
          lineWidthMinPixels: 1.2,
        }),
        new H3HexagonLayer<CellStat>({
          id: `hexes-r${res}`,
          data: cells,
          getHexagon: (d) => d.hex,
          extruded: mode === "3d",
          coverage: 0.9,
          getElevation: (d) => (Math.sqrt(d.n) / maxSqrt) * MAX_HEIGHT[res],
          getFillColor: (d) => sentimentColour(d.mean, d.n),
          getLineColor: [255, 255, 255, 160],
          lineWidthMinPixels: mode === "flat" ? 0.5 : 0,
          stroked: mode === "flat",
          material: { ambient: 0.55, diffuse: 0.6, shininess: 24, specularColor: [255, 255, 255] },
          pickable: true,
          autoHighlight: true,
          highlightColor: [242, 197, 49, 255],
          onHover: (info: PickingInfo<CellStat>) =>
            setHover(info.object ? { cell: info.object, x: info.x, y: info.y } : null),
          updateTriggers: { getElevation: [maxSqrt, res], getFillColor: [themeId, range] },
          transitions: prefersReducedMotion() ? undefined : { getElevation: 450 },
        }),
      ]
    : [];

  const themeLabel = data?.themes.find((t) => t.id === themeId)?.label ?? "";

  return (
    <div className="app">
      <div className="map" onMouseLeave={() => setHover(null)}>
        <DeckGL
          viewState={viewState}
          onViewStateChange={({ viewState: v }) => setViewState(v as MapViewState)}
          controller={{ dragRotate: mode === "3d" }}
          layers={layers}
        >
          <Map mapStyle={MAP_STYLE} attributionControl={{ compact: true }} />
        </DeckGL>
      </div>

      <div className="panel">
        <header className="notice">
          <p className="notice__kicker">Brighton &amp; Hove</p>
          <h1>Planning consultation themes</h1>
          <p className="notice__intro">
            Where issues raised in consultation responses cluster, how people feel about them, and how that
            changes over time.
          </p>
        </header>

        <div className="panel__body">
          {error && <p className="message message--error">{error}</p>}
          {!data && !error && <p className="message">Loading responses…</p>}
          {data && (
            <>
              <ThemeList
                themes={data.themes}
                totals={totalsByTheme}
                selected={themeId}
                onSelect={(id) => setThemeId(id)}
              />
              <Segmented<Resolution>
                label="Hex size"
                value={res}
                onChange={setRes}
                options={[
                  { value: 8, label: "Neighbourhood" },
                  { value: 9, label: "Street" },
                ]}
              />
              <Segmented<ViewMode>
                label="View"
                value={mode}
                onChange={changeMode}
                options={[
                  { value: "3d", label: "3D" },
                  { value: "flat", label: "Flat" },
                ]}
              />
              <p className="panel__footnote">
                Built on synthetic data: no real applications or responses are shown.{" "}
                {data.meta.attribution}
              </p>
            </>
          )}
        </div>
      </div>

      {data && agg && <Timeline months={agg.months} totals={monthTotals} range={range} onChange={setRange} />}
      {data && <Legend mode={mode} />}
      {hover && <HoverCard cell={hover.cell} x={hover.x} y={hover.y} themeLabel={themeLabel} />}
    </div>
  );
}
