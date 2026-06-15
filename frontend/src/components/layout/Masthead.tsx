"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/cn";
import { EditionDate } from "@/components/layout/EditionDate";

/** Navigation entries — each page is styled as a newspaper section. */
const NAV = [
  { href: "/", label: "Front Page" },
  { href: "/accounts", label: "The Index" },
  { href: "/enrich", label: "Stop the Press" },
];

function isActive(pathname: string, href: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

/** The newspaper masthead: title, edition metadata, and section navigation. */
export function Masthead() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b-4 border-ink bg-paper">
      <div className="mx-auto max-w-screen-xl px-4">
        {/* Edition metadata bar */}
        <div className="flex items-center justify-between border-b border-divider py-1.5">
          <p className="font-mono text-[10px] uppercase tracking-widest text-neutral-500">
            Vol. 1 &nbsp;|&nbsp; <EditionDate /> &nbsp;|&nbsp; New York Edition
          </p>
          <p className="hidden font-mono text-[10px] uppercase tracking-widest text-neutral-500 sm:block">
            All the Accounts That Are Fit to Pursue
          </p>
        </div>

        {/* Title */}
        <Link
          href="/"
          className="block py-4 text-center"
          onClick={() => setOpen(false)}
        >
          <h1 className="font-serif text-3xl font-black tracking-tight sm:text-5xl lg:text-6xl">
            THE LEAD INTELLIGENCE TIMES
          </h1>
        </Link>

        {/* Desktop section nav */}
        <nav
          aria-label="Primary"
          className="hidden items-center justify-center gap-8 border-t border-ink py-2 sm:flex"
        >
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(pathname, item.href) ? "page" : undefined}
              className={cn(
                "whitespace-nowrap font-mono text-xs uppercase tracking-widest transition-colors hover:text-accent",
                isActive(pathname, item.href)
                  ? "text-accent underline decoration-accent decoration-2 underline-offset-4"
                  : "text-ink",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Mobile nav toggle */}
        <div className="flex items-center justify-between border-t border-ink py-1 sm:hidden">
          <span className="font-mono text-[10px] uppercase tracking-widest text-neutral-500">
            Sections
          </span>
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close menu" : "Open menu"}
            className="flex min-h-[44px] min-w-[44px] items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ink"
          >
            {open ? <X className="h-5 w-5 stroke-1" /> : <Menu className="h-5 w-5 stroke-1" />}
          </button>
        </div>
      </div>

      {/* Mobile menu panel */}
      {open && (
        <nav
          id="mobile-nav"
          aria-label="Primary mobile"
          className="border-t border-ink bg-paper sm:hidden"
        >
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              aria-current={isActive(pathname, item.href) ? "page" : undefined}
              className={cn(
                "flex min-h-[44px] items-center border-b border-divider px-4 font-mono text-xs uppercase tracking-widest",
                isActive(pathname, item.href) ? "bg-ink text-paper" : "text-ink hover:bg-neutral-100",
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
