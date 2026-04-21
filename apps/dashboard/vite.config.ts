import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    fs: {
      allow: ["../.."]
    }
  },
  build: {
    sourcemap: true
  },
  test: {
    environment: "node",
    globals: true
  }
});
