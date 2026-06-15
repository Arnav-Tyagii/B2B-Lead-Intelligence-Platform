"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api";

interface FetchState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/**
 * Minimal data-fetching hook with loading/error state and a manual `reload`.
 *
 * We fetch on the client (not in a Server Component) on purpose: the Render
 * free tier cold-starts in ~50s, and client fetching lets us show Newsprint
 * loading skeletons immediately instead of blocking the whole page render.
 */
export function useFetch<T>(
  factory: () => Promise<T>,
  deps: React.DependencyList,
): FetchState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    factory()
      .then((d) => active && setData(d))
      .catch((e: unknown) => {
        if (!active) return;
        setData(null);
        setError(e instanceof ApiError ? e.message : "Something went wrong.");
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
    // factory is intentionally omitted; `deps` controls refetching.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return { data, error, loading, reload };
}
