import type { Stats } from "@/lib/types";
import { formatNumber, formatScore } from "@/lib/format";
import { SectionLabel } from "@/components/ui/SectionLabel";

function Kpi({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="px-6 py-8 text-center">
      <SectionLabel>{label}</SectionLabel>
      <p
        className={`mt-3 font-serif text-5xl font-black tabular-nums lg:text-6xl ${
          accent ? "text-accent" : "text-ink"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

/** Three headline KPIs in a collapsed-border row. */
export function KpiStats({ stats }: { stats: Stats }) {
  return (
    <div className="grid grid-cols-1 divide-y divide-ink border border-ink sm:grid-cols-3 sm:divide-x sm:divide-y-0">
      <Kpi label="Total Accounts" value={formatNumber(stats.total_accounts)} />
      <Kpi label="Hot Accounts" value={formatNumber(stats.hot_count)} accent />
      <Kpi label="Average Fit Score" value={`${formatScore(stats.average_score)}/100`} />
    </div>
  );
}
