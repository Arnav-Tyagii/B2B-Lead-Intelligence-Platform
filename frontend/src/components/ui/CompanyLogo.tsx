"use client";

import { useState } from "react";

/**
 * Real company icon, keyed by domain, from free key-less favicon services.
 * We try DuckDuckGo first (usually the cleaner brand mark), then Google as a
 * fallback, then monogram initials for unknown/synthetic domains — so the
 * layout never breaks. Grayscale to honour the Newsprint design system.
 *
 * (Clearbit's free logo API was retired after the HubSpot acquisition, so these
 * favicon endpoints are the reliable no-key replacement.)
 *
 * Plain <img> (not next/image) is deliberate: it avoids whitelisting external
 * hosts in next.config and the per-image optimization round-trip for a tiny icon.
 */
export function CompanyLogo({
  domain,
  name,
  size = 40,
  className = "",
}: {
  domain: string;
  name: string;
  size?: number;
  className?: string;
}) {
  const sources = [
    `https://icons.duckduckgo.com/ip3/${domain}.ico`,
    `https://www.google.com/s2/favicons?domain=${domain}&sz=128`,
  ];
  const [idx, setIdx] = useState(0);
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  if (idx >= sources.length) {
    return (
      <div
        aria-hidden="true"
        className={`flex items-center justify-center bg-neutral-200 font-serif font-bold text-neutral-500 ${className}`}
        style={{ width: size, height: size, fontSize: size * 0.4 }}
      >
        {initials}
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={sources[idx]}
      alt={`${name} logo`}
      width={size}
      height={size}
      loading="lazy"
      onError={() => setIdx((i) => i + 1)}
      className={`object-contain grayscale ${className}`}
      style={{ width: size, height: size }}
    />
  );
}
