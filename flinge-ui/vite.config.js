import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";

const root = path.dirname(fileURLToPath(import.meta.url));
const fruitless = path.resolve(root, "../try/fruitless");

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8765",
    },
    fs: {
      allow: [root, path.join(fruitless, "assets/fly"), path.join(fruitless, "experiment"), path.join(fruitless, "assets")],
    },
  },
});
