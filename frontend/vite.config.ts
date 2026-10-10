import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Frontend dev server proxies /api to the local backend, so the
// frontend code never needs to hard-code a backend host — change the
// target here (and VITE_API_BASE_URL for the built version) if your
// backend runs somewhere other than localhost:8000.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "https://shakir-voice-backend.onrender.com",
        // target: "http://127.0.0.1:8000",  
        changeOrigin: true,
      },
    },
  },
});
