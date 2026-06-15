"use client";

import Marquee from "react-fast-marquee";
import { useReducedMotion } from "@/lib/hooks";

export interface TickerItem {
  /** Short mono label, e.g. "HOT" or "AVG". */
  label: string;
  /** The value/text to display. */
  value: string;
  /** Highlight the label in editorial red (for breaking-news emphasis). */
  accent?: boolean;
}

/**
 * Breaking-news stock-ticker crawl. Black background, white text, red accent
 * badges — mimics a newsroom wire (DESIGN_SYSTEM.md "Marquee Ticker").
 */
export function StatTicker({ items }: { items: TickerItem[] }) {
  const reduced = useReducedMotion();
  if (items.length === 0) return null;
  return (
    <div className="border-y border-ink bg-ink text-paper">
      {/* Reduced-motion users get a static, non-scrolling crawl. */}
      <Marquee speed={40} gradient={false} pauseOnHover play={!reduced} aria-label="Account highlights ticker">
        {items.map((item, i) => (
          <span key={i} className="mx-8 inline-flex items-center gap-2 py-2">
            <span
              className={
                "font-mono text-[10px] font-medium uppercase tracking-widest " +
                (item.accent ? "bg-accent px-1.5 py-0.5 text-paper" : "text-neutral-400")
              }
            >
              {item.label}
            </span>
            <span className="font-sans text-sm">{item.value}</span>
            <span className="ml-6 text-neutral-600" aria-hidden="true">
              &#x2727;
            </span>
          </span>
        ))}
      </Marquee>
    </div>
  );
}
