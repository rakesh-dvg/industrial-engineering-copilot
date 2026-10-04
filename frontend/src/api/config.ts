/**
 * API base URL for browser fetch calls.
 *
 * - Production nginx (ALB or direct ECS): leave VITE_API_BASE_URL empty; browser
 *   calls same-origin /api/* and nginx proxies to BACKEND_API_URL.
 * - Local Vite dev: defaults to http://localhost:8020 unless overridden.
 * - Local UI + remote backend: set VITE_API_BASE_URL to the remote origin and
 *   VITE_DEV_API_PROXY=true so Vite proxies /api (avoids browser CORS).
 * - Cross-origin production (no nginx proxy): set VITE_API_BASE_URL at build time
 *   to the backend public URL (requires backend CORS; rebuild when the IP changes).
 */
function resolveApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  const useDevProxy =
    import.meta.env.DEV && import.meta.env.VITE_DEV_API_PROXY === "true";

  if (useDevProxy) {
    return "";
  }

  if (configured) {
    return configured.replace(/\/$/, "");
  }

  if (import.meta.env.DEV) {
    return "http://localhost:8020";
  }

  return "";
}

export const API_BASE_URL = resolveApiBaseUrl();
