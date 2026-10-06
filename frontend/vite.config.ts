import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/auth": "http://localhost:8000",
      "/chat": "http://localhost:8000",
      "/conversations": "http://localhost:8000",
      "/tickets": "http://localhost:8000",
      "/documents": "http://localhost:8000",
    },
  },
});
