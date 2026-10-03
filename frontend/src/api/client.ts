import { API_BASE_URL } from "./config";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as {
      error?: { code?: string; message?: string };
    };
    const message = body.error?.message ?? `Request failed with status ${response.status}`;
    return new ApiError(message, response.status, body.error?.code);
  } catch {
    return new ApiError(`Request failed with status ${response.status}`, response.status);
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (init?.body != null && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return (await response.json()) as T;
}
