import Link from "next/link";
import { Sparkles } from "lucide-react";
import type { Account } from "@/lib/types";
import { formatNumber, formatScore, formatUsd } from "@/lib/format";
import { Badge, tierTone } from "@/components/ui/Badge";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { CompanyLogo } from "@/components/ui/CompanyLogo";

/** A single account cell in The Index grid — links to its feature story. */
export function AccountCard({ account }: { account: Account }) {
  const { company, fit, enrichment } = account;
  return (
    <Link
      href={`/accounts/${encodeURIComponent(account.domain)}`}
      className="hard-shadow-hover group flex h-full flex-col bg-paper p-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2"
    >
      <div className="flex items-start justify-between gap-3">
        <SectionLabel>{company.industry}</SectionLabel>
        <div className="flex shrink-0 items-center gap-1.5">
          {company.is_real_data && (
            <span
              title="Real firmographics from SEC EDGAR filings"
              className="inline-flex items-center border border-ink px-1 py-0.5 font-mono text-[9px] font-medium uppercase tracking-widest text-ink"
            >
              SEC
            </span>
          )}
          {enrichment.source === "gemini" && (
            <span
              title="Enriched live by Gemini"
              className="inline-flex items-center gap-0.5 border border-accent px-1 py-0.5 font-mono text-[9px] font-medium uppercase tracking-widest text-accent"
            >
              <Sparkles className="h-2.5 w-2.5" aria-hidden="true" /> AI
            </span>
          )}
          <Badge tone={tierTone(fit.tier)}>{fit.tier}</Badge>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-3">
        <CompanyLogo
          domain={account.domain}
          name={company.name}
          size={36}
          className="shrink-0 border border-divider bg-paper p-0.5"
        />
        <h3 className="font-serif text-2xl font-bold leading-tight group-hover:text-accent">
          {company.name}
        </h3>
      </div>
      <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-neutral-500">
        {company.hq_location} · {company.country}
      </p>

      {/* Firmographics */}
      <dl className="mt-4 grid grid-cols-2 gap-2 font-mono text-[11px] text-neutral-600">
        <div>
          <dt className="uppercase tracking-wider text-neutral-400">Employees</dt>
          <dd className="text-ink">{formatNumber(company.employee_count)}</dd>
        </div>
        <div>
          <dt className="uppercase tracking-wider text-neutral-400">Revenue</dt>
          <dd className="text-ink">{formatUsd(company.estimated_revenue_usd)}</dd>
        </div>
      </dl>

      {/* Transparent score indicator */}
      <div className="mt-auto pt-5">
        <div className="flex items-baseline justify-between">
          <span className="font-mono text-[10px] uppercase tracking-widest text-neutral-400">
            Fit Score
          </span>
          <span className="font-serif text-xl font-black tabular-nums">
            {formatScore(fit.total)}
            <span className="text-sm text-neutral-400">/100</span>
          </span>
        </div>
        <div className="mt-1 h-1.5 w-full bg-divider" aria-hidden="true">
          <div
            className={`h-full ${fit.tier === "Hot" ? "bg-accent" : "bg-ink"}`}
            style={{ width: `${Math.min(100, fit.total)}%` }}
          />
        </div>
      </div>
    </Link>
  );
}
