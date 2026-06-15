"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";

/** The AI-drafted outreach email in a bordered, monospace "wire copy" block. */
export function OutreachBlock({ email }: { email: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(email);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable — no-op */
    }
  };

  return (
    <div className="border border-ink">
      <div className="flex items-center justify-between border-b border-ink bg-ink px-4 py-2 text-paper">
        <SectionLabel className="text-neutral-400">Drafted Outreach</SectionLabel>
        <button
          type="button"
          onClick={copy}
          aria-label="Copy outreach email"
          className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest transition-colors hover:text-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-paper"
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="whitespace-pre-wrap p-5 font-mono text-xs leading-relaxed text-neutral-700">
        {email}
      </pre>
    </div>
  );
}
