import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// dev: http://localhost:5173 proxies /api to Flask on :5000. build: bundle goes to ../static and is served by Flask at /static/.
export default defineConfig(({ command }) => ({
  plugins: [react()], base: command === "build" ? "/static/" : "/",
  build: { outDir: "../static", emptyOutDir: true },
  server: { port: 5173, proxy: { "/api": "http://localhost:5000" } },
}));
