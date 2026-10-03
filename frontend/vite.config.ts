import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, "");
  const proxyTarget = env.VITE_API_BASE_URL?.trim() || "http://localhost:8020";
  const useDevProxy = env.VITE_DEV_API_PROXY === "true";

  return {
    plugins: [react()],
    envDir: repoRoot,
    server: {
      port: 5173,
      host: true,
      proxy: useDevProxy
        ? {
            "/api": {
              target: proxyTarget,
              changeOrigin: true,
            },
            "/health": {
              target: proxyTarget,
              changeOrigin: true,
            },
          }
        : undefined,
    },
  };
});
