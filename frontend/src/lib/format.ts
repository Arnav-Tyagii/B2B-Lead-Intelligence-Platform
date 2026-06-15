/** Display formatters shared across the editorial UI. */

export function formatNumber(n: number): string {
  return n.toLocaleString("en-US");
}

/** Compact USD: $50M, $1.2B, $750K. */
export function formatUsd(n: number): string {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(n >= 1e10 ? 0 : 1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(0)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n}`;
}

export function formatScore(n: number): string {
  return Math.round(n).toString();
}

/** Today's edition date, e.g. "Monday, June 15, 2026". */
export function editionDate(): string {
  return new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}
