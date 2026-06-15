"use client";

import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { IndustryCount } from "@/lib/types";

const AXIS = { fontFamily: "JetBrains Mono, monospace", fontSize: 11, fill: "#737373" };

/** Horizontal bars of the top industries by account count. */
export function IndustryChart({ data }: { data: IndustryCount[] }) {
  const top = data.slice(0, 8);
  const summary = top.map((d) => `${d.industry}: ${d.count}`).join(", ");
  return (
    <div role="img" aria-label={`Top industries by account count — ${summary}`}>
    <ResponsiveContainer width="100%" height={Math.max(240, top.length * 32)}>
      <BarChart
        data={top}
        layout="vertical"
        margin={{ top: 0, right: 16, bottom: 0, left: 8 }}
        barCategoryGap={6}
      >
        <XAxis type="number" tick={AXIS} axisLine={false} tickLine={false} allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="industry"
          width={120}
          tick={AXIS}
          axisLine={{ stroke: "#111111" }}
          tickLine={false}
        />
        <Tooltip
          cursor={{ fill: "rgba(0,0,0,0.05)" }}
          contentStyle={{
            border: "1px solid #111111",
            borderRadius: 0,
            fontFamily: "JetBrains Mono, monospace",
            fontSize: 12,
          }}
        />
        <Bar dataKey="count" fill="#111111" isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
    </div>
  );
}
