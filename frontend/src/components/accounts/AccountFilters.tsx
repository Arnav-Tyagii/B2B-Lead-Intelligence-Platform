"use client";

import type { DataSource, EnrichmentSource, SortOrder, Tier } from "@/lib/types";
import { COUNTRIES } from "@/lib/constants";
import { Button } from "@/components/ui/Button";

export interface FilterValues {
  tier: Tier | "";
  industry: string;
  country: string;
  minScore: string;
  source: EnrichmentSource | "";
  dataSource: DataSource | "";
  sort: SortOrder;
}

const selectClass =
  "w-full border-b-2 border-ink bg-transparent px-1 py-2 font-mono text-sm focus-visible:bg-[#F0F0F0] focus-visible:outline-none";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block font-mono text-xs uppercase tracking-widest text-neutral-500">
        {label}
      </span>
      {children}
    </label>
  );
}

/** Server-side filter controls for The Index. Changes lift up to the page. */
export function AccountFilters({
  values,
  industries,
  onChange,
  onReset,
}: {
  values: FilterValues;
  industries: string[];
  onChange: (patch: Partial<FilterValues>) => void;
  onReset: () => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-4 border border-ink p-4 md:grid-cols-3 lg:grid-cols-4">
      <Field label="Tier">
        <select
          className={selectClass}
          value={values.tier}
          onChange={(e) => onChange({ tier: e.target.value as Tier | "" })}
        >
          <option value="">All</option>
          <option value="Hot">Hot</option>
          <option value="Warm">Warm</option>
          <option value="Cold">Cold</option>
        </select>
      </Field>

      <Field label="Industry">
        <select
          className={selectClass}
          value={values.industry}
          onChange={(e) => onChange({ industry: e.target.value })}
        >
          <option value="">All</option>
          {industries.map((i) => (
            <option key={i} value={i}>
              {i}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Country">
        <select
          className={selectClass}
          value={values.country}
          onChange={(e) => onChange({ country: e.target.value })}
        >
          <option value="">All</option>
          {COUNTRIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Min Score">
        <input
          type="number"
          min={0}
          max={100}
          placeholder="0"
          className={selectClass}
          value={values.minScore}
          onChange={(e) => onChange({ minScore: e.target.value })}
        />
      </Field>

      <Field label="Enrichment">
        <select
          className={selectClass}
          value={values.source}
          onChange={(e) => onChange({ source: e.target.value as EnrichmentSource | "" })}
        >
          <option value="">All Sources</option>
          <option value="gemini">AI (Gemini)</option>
          <option value="fallback">Heuristic</option>
        </select>
      </Field>

      <Field label="Data Source">
        <select
          className={selectClass}
          value={values.dataSource}
          onChange={(e) => onChange({ dataSource: e.target.value as DataSource | "" })}
        >
          <option value="">All Data</option>
          <option value="sec_edgar">Real (SEC)</option>
          <option value="synthetic">Synthetic</option>
        </select>
      </Field>

      <Field label="Sort">
        <select
          className={selectClass}
          value={values.sort}
          onChange={(e) => onChange({ sort: e.target.value as SortOrder })}
        >
          <option value="real_first">Real Data First</option>
          <option value="ai_first">AI-Enriched First</option>
          <option value="score_desc">Score: High → Low</option>
          <option value="score_asc">Score: Low → High</option>
        </select>
      </Field>

      <div className="flex items-end justify-between gap-3 lg:col-span-2">
        <p className="font-mono text-[10px] uppercase leading-tight tracking-widest text-neutral-400">
          Filtered &amp; sorted server-side
        </p>
        <Button variant="ghost" size="sm" onClick={onReset}>
          Reset
        </Button>
      </div>
    </div>
  );
}
