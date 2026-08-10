import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  server: {
    proxy: {
      // En desarrollo, la API corre en uvicorn (mismo puerto que el servicio
      // de producción, FITLOSOPHY_PORT del .env: esta máquina es las dos cosas).
      "/api": "http://localhost:10012",
    },
  },
});
