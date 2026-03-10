import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/",
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
  build: {
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          refine: [
            "@refinedev/core",
            "@refinedev/antd",
            "@refinedev/react-router",
            "antd",
            "@ant-design/icons",
          ],
        },
      },
    },
  },
});
