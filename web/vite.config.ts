import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The site is served from https://<user>.github.io/geospatial-consultation-analysis-app/,
// so every asset and data path is resolved relative to this base (locally too).
export default defineConfig({
  plugins: [react()],
  base: "/geospatial-consultation-analysis-app/",
  build: { chunkSizeWarningLimit: 2000 }, // deck.gl and MapLibre are large by nature
});
