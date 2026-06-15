"use client";

import Link from "next/link";
import { api } from "@/lib/api";
import { useFetch } from "@/lib/useFetch";
import type { PaginatedAccounts, Stats } from "@/lib/types";
import { formatScore } from "@/lib/format";
import { EditionDate } from "@/components/layout/EditionDate";
import { Button } from "@/components/ui/Button";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { Divider } from "@/components/ui/Divider";
import { StatTicker, type TickerItem } from "@/components/ui/StatTicker";
import { Skeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorState } from "@/components/system/StateViews";
import { KpiStats } from "@/components/dashboard/KpiStats";
import { TierChart } from "@/components/dashboard/TierChart";
import { IndustryChart } from "@/components/dashboard/IndustryChart";

export default function DashboardPage() {
  const stats = useFetch<Stats>(() => api.getStats(), []);
  const topHot = useFetch<PaginatedAccounts>(
    () => api.getAccounts({ tier: "Hot", sort: "score_desc", page_size: 8 }),
    [],
  );

  const tickerItems: TickerItem[] = (() => {
    if (!stats.data) return [];
    const base: TickerItem[] = [
      { label: "Breaking", value: `${stats.data.total_accounts} accounts scored against ICP`, accent: true },
      { label: "Hot", value: `${stats.data.hot_count} high-fit accounts`, accent: true },
      { label: "Avg Fit", value: `${formatScore(stats.data.average_score)} / 100` },
    ];
    const hot =
      topHot.data?.items.map<TickerItem>((a) => ({
        label: a.company.industry,
        value: `${a.company.name} — ${formatScore(a.fit.total)}`,
      })) ?? [];
    return [...base, ...hot];
  })();

  return (
    <>
      {tickerItems.length > 0 && <StatTicker items={tickerItems} />}

      <div className="mx-auto max-w-screen-xl px-4 py-10">
        {/* ── Lede ── */}
        <SectionLabel>
          <EditionDate /> · The Front Page
        </SectionLabel>
        <h2 className="mt-2 max-w-4xl font-serif text-5xl font-black leading-[0.9] tracking-tight lg:text-7xl">
          The Book of Business, Ranked by Fit
        </h2>
        <p className="drop-cap mt-6 max-w-2xl font-body text-lg leading-relaxed text-neutral-700">
          Every account in the index has been enriched with go-to-market
          intelligence and scored against the Ideal Customer Profile. The hottest
          opportunities lead the page; the full index lies within.
        </p>

        <Divider />

        {/* ── KPIs ── */}
        {stats.loading && <Skeleton className="h-40 w-full" />}
        {stats.error && <ErrorState message={stats.error} onRetry={stats.reload} />}
        {stats.data && <KpiStats stats={stats.data} />}

        {/* ── Charts ── */}
        {stats.data && (
          <div className="mt-px grid grid-cols-1 border border-ink lg:grid-cols-12">
            <section className="border-b border-ink p-6 lg:col-span-5 lg:border-b-0 lg:border-r">
              <SectionLabel>Distribution by Tier</SectionLabel>
              <div className="mt-4">
                <TierChart data={stats.data.tier_distribution} />
              </div>
            </section>
            <section className="p-6 lg:col-span-7">
              <SectionLabel>Top Industries in the Book</SectionLabel>
              <div className="mt-4">
                <IndustryChart data={stats.data.industry_distribution} />
              </div>
            </section>
          </div>
        )}

        <Divider />

        {/* ── Inverted (black) section: How it works, with red numbered steps ── */}
        <section className="newsprint-texture bg-ink px-6 py-12 text-paper lg:px-12">
          <SectionLabel className="text-neutral-400">The Method</SectionLabel>
          <h3 className="mt-2 font-serif text-3xl font-black lg:text-4xl">
            How Every Account Earns Its Score
          </h3>
          <ol className="mt-8 grid grid-cols-1 gap-8 md:grid-cols-3">
            {[
              ["01", "Acquire", "Firmographics for every company — industry, size, revenue, geography."],
              ["02", "Enrich", "GenAI infers technographics, intent signals, pain points, and outreach."],
              ["03", "Score", "A transparent ICP engine ranks fit 0–100 with a full breakdown."],
            ].map(([num, title, body]) => (
              <li key={num} className="border-t-2 border-neutral-700 pt-4">
                <span className="font-mono text-2xl font-bold text-accent">{num}</span>
                <h4 className="mt-2 font-serif text-xl font-bold">{title}</h4>
                <p className="mt-2 font-body text-sm text-neutral-400">{body}</p>
              </li>
            ))}
          </ol>
          <Link href="/accounts" className="mt-10 inline-block">
            <Button variant="secondary" className="border-paper text-paper hover:bg-paper hover:text-ink">
              Read The Index
            </Button>
          </Link>
        </section>
      </div>
    </>
  );
}
