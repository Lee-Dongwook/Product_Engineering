export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(`요청에 실패했습니다. (${status})`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetcher<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let body: { detail?: unknown } | undefined;

    try {
      body = await response.json();
    } catch {
      //WIP
    }

    throw new ApiError(response.status, body?.detail ?? null);
  }

  return response.json();
}
