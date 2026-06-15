"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

/** Server-side pagination control. */
export function Pagination({
  page,
  totalPages,
  total,
  onPage,
}: {
  page: number;
  totalPages: number;
  total: number;
  onPage: (p: number) => void;
}) {
  if (totalPages <= 1) return null;
  return (
    <nav
      aria-label="Pagination"
      className="flex items-center justify-between border-t border-ink py-4"
    >
      <button
        type="button"
        onClick={() => onPage(page - 1)}
        disabled={page <= 1}
        aria-label="Previous page"
        className="inline-flex min-h-[44px] items-center gap-1 px-3 font-mono text-xs uppercase tracking-widest transition-colors hover:text-accent disabled:pointer-events-none disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
      >
        <ChevronLeft className="h-4 w-4 stroke-1" /> Prev
      </button>

      <p className="font-mono text-xs uppercase tracking-widest text-neutral-500">
        Page {page} of {totalPages}
        <span className="hidden sm:inline"> · {total} accounts</span>
      </p>

      <button
        type="button"
        onClick={() => onPage(page + 1)}
        disabled={page >= totalPages}
        aria-label="Next page"
        className="inline-flex min-h-[44px] items-center gap-1 px-3 font-mono text-xs uppercase tracking-widest transition-colors hover:text-accent disabled:pointer-events-none disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
      >
        Next <ChevronRight className="h-4 w-4 stroke-1" />
      </button>
    </nav>
  );
}
