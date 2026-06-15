import type { FitBreakdown } from "@/lib/types";

/**
 * ICP weight per scoring dimension (the max points each can earn). Mirrors the
 * backend default ICP weights and is used to render the transparent score-
 * breakdown bars as points-out-of-weight.
 */
export const FIT_WEIGHTS: Record<keyof FitBreakdown, number> = {
  industry: 25,
  company_size: 20,
  revenue: 15,
  geography: 10,
  technographics: 15,
  intent: 15,
};

/** Ordered, labeled dimensions for the breakdown UI. */
export const FIT_DIMENSIONS: { key: keyof FitBreakdown; label: string }[] = [
  { key: "industry", label: "Industry" },
  { key: "company_size", label: "Company Size" },
  { key: "revenue", label: "Revenue" },
  { key: "geography", label: "Geography" },
  { key: "technographics", label: "Technographics" },
  { key: "intent", label: "Intent" },
];

/** Country options for filters (matches the seed generator's spread). */
export const COUNTRIES = [
  "United States",
  "United Kingdom",
  "Canada",
  "India",
  "Germany",
  "Australia",
  "Singapore",
  "Brazil",
];

/** Industry options for the live-enrich form (ICP target verticals + a few). */
export const INDUSTRIES = [
  "SaaS",
  "FinTech",
  "Cybersecurity",
  "MarTech",
  "Cloud Infrastructure",
  "E-commerce",
  "HR Tech",
  "Data & Analytics",
  "Manufacturing",
  "Healthcare",
  "Retail",
  "Logistics",
];

export const PAGE_SIZE = 12;
