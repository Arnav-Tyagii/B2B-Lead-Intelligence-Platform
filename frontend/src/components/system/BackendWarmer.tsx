"use client";

import { useEffect } from "react";
import { api } from "@/lib/api";

/**
 * Pings /health once on first load to wake the Render free-tier backend before
 * the user navigates to a data page. Renders nothing.
 */
export function BackendWarmer() {
  useEffect(() => {
    api.warm();
  }, []);
  return null;
}
