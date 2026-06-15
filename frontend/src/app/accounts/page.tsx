"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useFetch } from "@/lib/useFetch";
import { useDebounce } from "@/lib/hooks";
import type { PaginatedAccounts, AccountsParams } from "@/lib/types";
import { INDUSTRIES, PAGE_SIZE } from "@/lib/constants";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { CardSkeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorState, EmptyState } from "@/components/system/StateViews";
import { AccountCard } from "@/components/accounts/AccountCard";
import { AccountFilters, type FilterValues } from "@/components/accounts/AccountFilters";
import { Pagination } from "@/components/accounts/Pagination";

const DEFAULT_FILTERS: FilterValues = {
  tier: "",
  industry: "",
  country: "",
  minScore: "",
  source: "",
  // Default to AI-first so genuinely Gemini-enriched accounts lead the book.
  sort: "ai_first",
};

export default function AccountsPage() {
  const [filters, setFilters] = useState<FilterValues>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);

  // Debounce the free-text min-score input so typing doesn't refetch per keystroke.
  const debouncedMinScore = useDebounce(filters.minScore, 350);

  // Build the server-side query from the current filter state.
  const minScoreNum = debouncedMinScore === "" ? undefined : Number(debouncedMinScore);
  const params: AccountsParams = {
    page,
    page_size: PAGE_SIZE,
    tier: filters.tier || undefined,
    industry: filters.industry || undefined,
    country: filters.country || undefined,
    min_score: Number.isFinite(minScoreNum) ? minScoreNum : undefined,
    source: filters.source || undefined,
    sort: filters.sort,
  };

  const { data, error, loading, reload } = useFetch<PaginatedAccounts>(
    () => api.getAccounts(params),
    [
      page,
      filters.tier,
      filters.industry,
      filters.country,
      debouncedMinScore,
      filters.source,
      filters.sort,
    ],
  );

  // Any filter change resets to page 1.
  const patchFilters = (patch: Partial<FilterValues>) => {
    setFilters((f) => ({ ...f, ...patch }));
    setPage(1);
  };
  const resetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-10">
      <SectionLabel>The Index</SectionLabel>
      <h2 className="mt-2 font-serif text-5xl font-black tracking-tight lg:text-6xl">
        The Book of Accounts
      </h2>
      <p className="mt-3 max-w-2xl font-body text-neutral-600">
        Filtered, sorted, and paginated server-side. Select a story to read the
        full account profile.
      </p>

      <div className="mt-6">
        <AccountFilters
          values={filters}
          industries={INDUSTRIES}
          onChange={patchFilters}
          onReset={resetFilters}
        />
      </div>

      <div className="mt-6">
        {loading && (
          <div className="grid grid-cols-1 gap-px border border-ink bg-ink sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: PAGE_SIZE }).map((_, i) => (
              <div key={i} className="bg-paper">
                <CardSkeleton />
              </div>
            ))}
          </div>
        )}

        {!loading && error && <ErrorState message={error} onRetry={reload} />}

        {!loading && !error && data && data.items.length === 0 && (
          <EmptyState message="No accounts match these filters. Try widening your criteria." />
        )}

        {!loading && !error && data && data.items.length > 0 && (
          <>
            <div className="grid grid-cols-1 gap-px border border-ink bg-ink sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {data.items.map((account) => (
                <AccountCard key={account.domain} account={account} />
              ))}
            </div>
            <Pagination
              page={data.page}
              totalPages={data.total_pages}
              total={data.total}
              onPage={setPage}
            />
          </>
        )}
      </div>
    </div>
  );
}
