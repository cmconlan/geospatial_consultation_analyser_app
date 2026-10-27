import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base: assets and data load relative to index.html, so the site works
// at any path (GitHub Pages under any repo name, or locally at the root).
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { chunkSizeWarningLimit: 2000 }, // deck.gl and MapLibre are large by nature
});