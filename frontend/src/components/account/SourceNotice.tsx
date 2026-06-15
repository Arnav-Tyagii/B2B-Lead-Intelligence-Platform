import { Sparkles, Cpu } from "lucide-react";
import type { EnrichmentSource } from "@/lib/types";

/**
 * Honestly disclose how the enrichment was produced. When Gemini's free-tier
 * quota is exhausted, the platform falls back to a deterministic estimate — we
 * say so plainly rather than passing it off as live AI.
 */
export function SourceNotice({ source }: { source: EnrichmentSource }) {
  if (source === "gemini") {
    return (
      <div className="flex items-center gap-2 border border-ink bg-paper px-3 py-2 font-mono text-[11px] uppercase tracking-widest">
        <Sparkles className="h-4 w-4 stroke-1 text-accent" aria-hidden="true" />
        Enriched live by Gemini
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 border border-divider bg-neutral-100 px-3 py-2 font-mono text-[11px] uppercase tracking-widest text-neutral-600">
      <Cpu className="h-4 w-4 stroke-1" aria-hidden="true" />
      Deterministic estimate (live AI quota unavailable)
    </div>
  );
}
