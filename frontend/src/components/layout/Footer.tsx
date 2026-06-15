/** Newspaper colophon footer with edition metadata. */
export function Footer() {
  return (
    <footer className="mt-16 border-t-4 border-ink bg-paper">
      <div className="mx-auto flex max-w-screen-xl flex-col items-center gap-2 px-4 py-8 text-center">
        <p className="font-serif text-2xl font-bold">THE LEAD INTELLIGENCE TIMES</p>
        <p className="font-mono text-[10px] uppercase tracking-widest text-neutral-500">
          Edition: Vol 1.0 &nbsp;|&nbsp; Printed in NYC &nbsp;|&nbsp; Account-Based GTM Intelligence
        </p>
        <p className="max-w-md font-body text-xs text-neutral-500">
          A demonstration platform. Firmographics are synthetic; enrichment is
          produced by Gemini or a deterministic fallback.
        </p>
      </div>
    </footer>
  );
}
