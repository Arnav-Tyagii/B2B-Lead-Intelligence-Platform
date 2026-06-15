"use client";

import { useState, type FormEvent } from "react";
import { api, ApiError } from "@/lib/api";
import type { Account, EnrichRequest } from "@/lib/types";
import { COUNTRIES, INDUSTRIES } from "@/lib/constants";
import { Button } from "@/components/ui/Button";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { Divider } from "@/components/ui/Divider";
import { Skeleton } from "@/components/ui/LoadingSkeleton";
import { ErrorState } from "@/components/system/StateViews";
import { AccountFeature } from "@/components/account/AccountFeature";

const inputClass =
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

export default function EnrichPage() {
  const [form, setForm] = useState({
    domain: "",
    name: "",
    industry: "",
    employee_count: "",
    estimated_revenue_usd: "",
    country: "",
    hq_location: "",
    recent_news: "",
  });
  const [result, setResult] = useState<Account | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (k: keyof typeof form, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.domain.trim()) {
      setError("A company domain is required to run enrichment.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    const num = (v: string) => (v.trim() === "" ? undefined : Number(v));
    const body: EnrichRequest = {
      domain: form.domain.trim(),
      name: form.name.trim() || undefined,
      industry: form.industry || undefined,
      employee_count: num(form.employee_count),
      estimated_revenue_usd: num(form.estimated_revenue_usd),
      country: form.country || undefined,
      hq_location: form.hq_location.trim() || undefined,
      recent_news: form.recent_news
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean),
    };

    try {
      const account = await api.enrich(body);
      setResult(account);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Enrichment failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-10">
      <SectionLabel>Stop the Press</SectionLabel>
      <h2 className="mt-2 font-serif text-5xl font-black tracking-tight lg:text-6xl">
        Enrich an Account, Live
      </h2>
      <p className="mt-3 max-w-2xl font-body text-neutral-600">
        Submit a company profile to run a single on-demand Gemini enrichment and
        ICP score. If the live AI quota is unavailable, the platform falls back to
        a deterministic estimate — and tells you so.
      </p>

      <form
        onSubmit={onSubmit}
        className="mt-8 grid grid-cols-1 gap-5 border border-ink p-6 md:grid-cols-2"
      >
        <Field label="Domain *">
          <input
            className={inputClass}
            placeholder="acme.com"
            value={form.domain}
            onChange={(e) => set("domain", e.target.value)}
            required
          />
        </Field>
        <Field label="Company Name">
          <input
            className={inputClass}
            placeholder="Acme Inc."
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
          />
        </Field>
        <Field label="Industry">
          <select
            className={inputClass}
            value={form.industry}
            onChange={(e) => set("industry", e.target.value)}
          >
            <option value="">Auto (SaaS)</option>
            {INDUSTRIES.map((i) => (
              <option key={i} value={i}>
                {i}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Country">
          <select
            className={inputClass}
            value={form.country}
            onChange={(e) => set("country", e.target.value)}
          >
            <option value="">Auto (United States)</option>
            {COUNTRIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Employees">
          <input
            type="number"
            min={0}
            className={inputClass}
            placeholder="500"
            value={form.employee_count}
            onChange={(e) => set("employee_count", e.target.value)}
          />
        </Field>
        <Field label="Est. Revenue (USD)">
          <input
            type="number"
            min={0}
            className={inputClass}
            placeholder="50000000"
            value={form.estimated_revenue_usd}
            onChange={(e) => set("estimated_revenue_usd", e.target.value)}
          />
        </Field>
        <Field label="HQ Location">
          <input
            className={inputClass}
            placeholder="San Francisco, CA"
            value={form.hq_location}
            onChange={(e) => set("hq_location", e.target.value)}
          />
        </Field>
        <Field label="Recent News (one per line)">
          <textarea
            className={`${inputClass} min-h-[44px] resize-y`}
            rows={2}
            placeholder="Acme raised a $20M Series B."
            value={form.recent_news}
            onChange={(e) => set("recent_news", e.target.value)}
          />
        </Field>

        <div className="md:col-span-2">
          <Button type="submit" disabled={loading} className="w-full md:w-auto">
            {loading ? "Printing…" : "Run Enrichment"}
          </Button>
        </div>
      </form>

      <Divider />

      {loading && (
        <div className="space-y-4">
          <p className="font-mono text-xs uppercase tracking-widest text-neutral-500">
            Contacting the newsroom — a cold backend or AI rate-limit may add a moment…
          </p>
          <Skeleton className="h-16 w-3/4" />
          <Skeleton className="h-56 w-full" />
        </div>
      )}

      {!loading && error && <ErrorState message={error} onRetry={() => setError(null)} />}

      {!loading && !error && result && <AccountFeature account={result} />}
    </div>
  );
}
