"use client";

import { useEffect, useState } from "react";
import { editionDate } from "@/lib/format";

/**
 * Renders today's date on the client after mount.
 *
 * Why client-side: pages are statically prerendered, so a server-rendered
 * `new Date()` would freeze at BUILD time and show a stale edition date in
 * production. Starting empty (matching SSR) then filling in on mount avoids a
 * hydration mismatch while keeping the masthead's date current per visit.
 */
export function EditionDate() {
  const [date, setDate] = useState("");
  useEffect(() => setDate(editionDate()), []);
  // Reserve space with a non-breaking space until mounted to avoid layout shift.
  return <span>{date || " "}</span>;
}
