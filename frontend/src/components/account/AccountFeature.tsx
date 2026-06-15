import type { Account } from "@/lib/types";
import { formatNumber, formatUsd } from "@/lib/format";
import { Badge, tierTone } from "@/components/ui/Badge";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { Divider } from "@/components/ui/Divider";
import { ScoreBreakdown } from "@/components/account/ScoreBreakdown";
import { OutreachBlock } from "@/components/account/OutreachBlock";
import { SourceNotice } from "@/components/account/SourceNotice";
import { CompanyLogo } from "@/components/ui/CompanyLogo";

function TagList({ items }: { items: string[] }) {
  return (
    <ul className="flex flex-wrap gap-2">
      {items.map((t, i) => (
        <li
          key={i}
          className="border border-ink px-2 py-1 font-mono text-[11px] uppercase tracking-wider"
        >
          {t}
        </li>
      ))}
    </ul>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-2">
      {items.map((t, i) => (
        <li key={i} className="flex gap-2 font-body text-sm leading-relaxed text-neutral-700">
          <span className="mt-1 select-none text-accent" aria-hidden="true">
            &#x2727;
          </span>
          <span>{t}</span>
        </li>
      ))}
    </ul>
  );
}

/** The full editorial "Feature Story" for one account. */
export function AccountFeature({ account }: { account: Account }) {
  const { company, enrichment, fit } = account;
  const isReal = company.data_source === "sec_edgar";

  return (
    <article>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SectionLabel>
          {company.industry} Bureau · {company.country}
        </SectionLabel>
        <div className="flex items-center gap-2">
          <Badge tone={tierTone(fit.tier)}>{fit.tier} Account</Badge>
          <SourceNotice source={enrichment.source} />
        </div>
      </div>

      <h1 className="mt-3 font-serif text-5xl font-black leading-[0.95] tracking-tight sm:text-6xl lg:text-7xl">
        {company.name}
      </h1>
      <p className="mt-3 border-y border-divider py-2 font-mono text-[11px] uppercase tracking-widest text-neutral-500">
        By The Intelligence Desk &nbsp;·&nbsp; {company.domain}
        {company.founded_year ? ` · Est. ${company.founded_year}` : ""}
      </p>

      <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Main column */}
        <div className="lg:col-span-8">
          {/* Image placeholder — grayscale halftone with Fig caption */}
          <figure className="border border-ink">
            <div className="halftone flex h-56 items-center justify-center bg-neutral-200">
              <CompanyLogo domain={account.domain} name={company.name} size={120} />
            </div>
            <figcaption className="border-t border-ink px-3 py-1.5 font-mono text-[10px] uppercase tracking-widest text-neutral-500">
              Fig. 1.1 — {company.name}, {company.hq_location}
            </figcaption>
          </figure>

          {company.description && (
            <p className="drop-cap mt-6 text-justify font-body text-lg leading-relaxed text-neutral-800">
              {company.description}
            </p>
          )}

          {enrichment.technographics.length > 0 && (
            <section className="mt-8">
              <SectionLabel>Technographics</SectionLabel>
              <div className="mt-3">
                <TagList items={enrichment.technographics} />
              </div>
            </section>
          )}

          <div className="mt-8 grid grid-cols-1 gap-8 sm:grid-cols-2">
            {enrichment.intent_signals.length > 0 && (
              <section>
                <SectionLabel>Intent Signals</SectionLabel>
                <div className="mt-3">
                  <BulletList items={enrichment.intent_signals} />
                </div>
              </section>
            )}
            {enrichment.pain_points.length > 0 && (
              <section>
                <SectionLabel>Pain Points</SectionLabel>
                <div className="mt-3">
                  <BulletList items={enrichment.pain_points} />
                </div>
              </section>
            )}
          </div>

          {enrichment.gtm_recommendation && (
            <section className="mt-8 border-l-4 border-accent bg-neutral-100 p-5">
              <SectionLabel>GTM Recommendation</SectionLabel>
              <p className="mt-2 font-body text-base leading-relaxed text-neutral-800">
                {enrichment.gtm_recommendation}
              </p>
            </section>
          )}

          {enrichment.outreach_email && (
            <section className="mt-8">
              <OutreachBlock email={enrichment.outreach_email} />
            </section>
          )}
        </div>

        {/* Sidebar */}
        <aside className="lg:col-span-4">
          <div className="border border-ink">
            <div className="border-b border-ink bg-ink px-4 py-2">
              <SectionLabel className="text-neutral-400">Firmographics</SectionLabel>
            </div>
            <dl className="divide-y divide-divider">
              {[
                ["Industry", company.industry],
                ["Employees", formatNumber(company.employee_count)],
                ["Est. Revenue", formatUsd(company.estimated_revenue_usd)],
                ["HQ", company.hq_location],
                ["Country", company.country],
                ["Founded", company.founded_year ? String(company.founded_year) : "—"],
                ["Data Source", isReal ? "SEC EDGAR" : "Synthetic"],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between gap-4 px-4 py-2.5">
                  <dt className="font-mono text-[11px] uppercase tracking-wider text-neutral-500">
                    {label}
                  </dt>
                  <dd className="text-right font-body text-sm text-ink">{value}</dd>
                </div>
              ))}
            </dl>
            {/* Provenance caption so each section's origin is auditable. */}
            <p className="border-t border-divider px-4 py-2 font-mono text-[10px] uppercase leading-relaxed tracking-widest text-neutral-400">
              {isReal
                ? "Source: SEC EDGAR filings · headcount approximate where unfiled"
                : "Source: synthetic generator"}
            </p>
          </div>

          <div className="mt-6">
            <ScoreBreakdown fit={fit} />
          </div>

          {company.recent_news.length > 0 && (
            <div className="mt-6 border border-divider p-4">
              <SectionLabel>{isReal ? "Hiring Signals" : "From the Wire"}</SectionLabel>
              {isReal && (
                <p className="mt-1 font-mono text-[10px] uppercase tracking-widest text-accent">
                  Live · Greenhouse / Lever job boards
                </p>
              )}
              <ul className="mt-3 space-y-2">
                {company.recent_news.map((n, i) => (
                  <li key={i} className="font-body text-sm italic leading-relaxed text-neutral-600">
                    “{n}”
                  </li>
                ))}
              </ul>
            </div>
          )}
        </aside>
      </div>

      <Divider />
    </article>
  );
}
