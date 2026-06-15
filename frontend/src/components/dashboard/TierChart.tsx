"use client";

import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TierCount } from "@/lib/types";

// Tier colors: Hot = editorial red, Warm = ink, Cold = quiet grey.
const TIER_COLORS: Record<string, string> = {
  Hot: "#CC0000",
  Warm: "#111111",
  Cold: "#A3A3A3",
};

const AXIS = { fontFamily: "JetBrains Mono, monospace", fontSize: 11, fill: "#737373" };

export function TierChart({ data }: { data: TierCount[] }) {
  const summary = data.map((d) => `${d.tier}: ${d.count}`).join(", ");
  return (
    <div role="img" aria-label={`Accounts by tier — ${summary}`}>
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
        <XAxis dataKey="tier" tick={AXIS} axisLine={{ stroke: "#111111" }} tickLine={false} />
        <YAxis tick={AXIS} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip
          cursor={{ fill: "rgba(0,0,0,0.05)" }}
          contentStyle={{
            border: "1px solid #111111",
            borderRadius: 0,
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 12,
          }}
        />
        <Bar dataKey="count" isAnimationActive={false}>
          {data.map((d) => (
            <Cell key={d.tier} fill={TIER_COLORS[d.tier] ?? "#111111"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
    </div>
  );
}
