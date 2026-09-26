import { apiFetch } from "./client";

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export interface DependencyHealth {
  status: string;
  message?: string | null;
}

export interface ApiHealthResponse extends HealthStatus {
  dependencies: Record<string, DependencyHealth>;
}

export function fetchRootHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>("/health");
}

export function fetchApiHealth(): Promise<ApiHealthResponse> {
  return apiFetch<ApiHealthResponse>("/api/v1/health");
}
