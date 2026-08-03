import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [svelte(), tailwindcss()],
  server: {
    proxy: {
      // En desarrollo, la API corre en uvicorn (puerto 8000).
      "/api": "http://localhost:8000",
    },
  },
});
