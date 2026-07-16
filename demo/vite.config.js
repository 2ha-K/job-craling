import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // Avoid Vite spawning `net use` while resolving real paths on Windows.
    preserveSymlinks: true,
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:4141",
        changeOrigin: true,
      },
    },
  },
});
