/**
 * Single typed API client for the FastAPI backend.
 *
 * Every network call funnels through `request()` so error handling and the
 * base URL live in one place. Errors become a friendly `ApiError` the UI can
 * render — including the common "backend is cold-starting" case on Render free
 * tier, which surfaces as a network failure.
 */

import type {
  Account,
  AccountsParams,
  EnrichRequest,
  PaginatedAccounts,
  Stats,
} from "@/lib/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    // fetch rejects on network failure — most often a cold backend.
    throw new ApiError(
      "Couldn't reach the server. It may be waking up from sleep — please retry in a moment.",
      0,
    );
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      /* non-JSON error body — keep the generic message */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json() as Promise<T>;
}

function toQuery(params: AccountsParams): string {
  const q = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
  });
  const s = q.toString();
  return s ? `?${s}` : "";
}

export const api = {
  /** Fire-and-forget warm-up so the first real call is fast. */
  warm(): void {
    fetch(`${BASE_URL}/health`).catch(() => {
      /* best effort */
    });
  },

  getStats(): Promise<Stats> {
    return request<Stats>("/stats");
  },

  getAccounts(params: AccountsParams = {}): Promise<PaginatedAccounts> {
    return request<PaginatedAccounts>(`/accounts${toQuery(params)}`);
  },

  getAccount(domain: string): Promise<Account> {
    return request<Account>(`/accounts/${encodeURIComponent(domain)}`);
  },

  enrich(body: EnrichRequest): Promise<Account> {
    return request<Account>("/enrich", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
};
