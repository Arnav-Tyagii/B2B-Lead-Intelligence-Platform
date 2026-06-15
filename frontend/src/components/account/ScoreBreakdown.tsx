import type { Fit } from "@/lib/types";
import { FIT_DIMENSIONS, FIT_WEIGHTS } from "@/lib/constants";
import { formatScore } from "@/lib/format";
import { SectionLabel } from "@/components/ui/SectionLabel";

/**
 * Transparent score breakdown: each dimension's earned points out of its ICP
 * weight, with a bar showing the ratio. This is the product's core promise —
 * the score is never a black box.
 */
export function ScoreBreakdown({ fit }: { fit: Fit }) {
  return (
    <div className="border border-ink p-6">
      <div className="flex items-baseline justify-between border-b border-divider pb-4">
        <SectionLabel>ICP Fit Breakdown</SectionLabel>
        <p className="font-serif text-3xl font-black tabular-nums">
          {formatScore(fit.total)}
          <span className="text-base text-neutral-400">/100</span>
        </p>
      </div>

      <ul className="mt-4 space-y-3">
        {FIT_DIMENSIONS.map(({ key, label }) => {
          const earned = fit.breakdown[key];
          const max = FIT_WEIGHTS[key];
          const pct = max > 0 ? (earned / max) * 100 : 0;
          return (
            <li key={key}>
              <div className="flex items-center justify-between font-mono text-[11px] uppercase tracking-wider">
                <span className="text-neutral-600">{label}</span>
                <span className="tabular-nums text-ink">
                  {earned} / {max}
                </span>
              </div>
              <div className="mt-1 h-2 w-full bg-divider" aria-hidden="true">
                <div className="h-full bg-ink" style={{ width: `${Math.min(100, pct)}%` }} />
              </div>
            </li>
          );
        })}
      </ul>

      {fit.rationale && (
        <p className="mt-5 border-t border-divider pt-4 font-body text-sm leading-relaxed text-neutral-600">
          {fit.rationale}
        </p>
      )}
    </div>
  );
}
