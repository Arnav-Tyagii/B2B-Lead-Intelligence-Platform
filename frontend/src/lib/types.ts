/**
 * TypeScript mirror of the backend pydantic schemas (app/models/*).
 * Keep these in sync with the API so the contract is type-safe end to end.
 */

export type Tier = "Hot" | "Warm" | "Cold";
export type EnrichmentSource = "gemini" | "fallback";
/** Firmographic provenance: where the company data came from. */
export type DataSource = "synthetic" | "sec_edgar";
export type SortOrder = "score_desc" | "score_asc" | "ai_first" | "real_first";

export interface Company {
  name: string;
  domain: string;
  industry: string;
  employee_count: number;
  estimated_revenue_usd: number;
  hq_location: string;
  country: string;
  founded_year: number | null;
  description: string;
  recent_news: string[];
  data_source: DataSource;
  /** Computed on the backend: true for real (non-synthetic) firmographics. */
  is_real_data: boolean;
}

export interface Enrichment {
  technographics: string[];
  intent_signals: string[];
  intent_topics: string[];
  pain_points: string[];
  outreach_email: string;
  gtm_recommendation: string;
  source: EnrichmentSource;
}

export interface FitBreakdown {
  industry: number;
  company_size: number;
  revenue: number;
  geography: number;
  technographics: number;
  intent: number;
}

export interface Fit {
  total: number;
  tier: Tier;
  breakdown: FitBreakdown;
  rationale: string;
}

export interface Account {
  domain: string;
  company: Company;
  enrichment: Enrichment;
  fit: Fit;
}

export interface PaginatedAccounts {
  items: Account[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TierCount {
  tier: Tier;
  count: number;
}

export interface IndustryCount {
  industry: string;
  count: number;
}

export interface Stats {
  total_accounts: number;
  hot_count: number;
  average_score: number;
  tier_distribution: TierCount[];
  industry_distribution: IndustryCount[];
}

export interface EnrichRequest {
  domain: string;
  name?: string;
  industry?: string;
  employee_count?: number;
  estimated_revenue_usd?: number;
  hq_location?: string;
  country?: string;
  founded_year?: number;
  description?: string;
  recent_news?: string[];
}

export interface AccountsParams {
  page?: number;
  page_size?: number;
  tier?: Tier;
  industry?: string;
  country?: string;
  min_score?: number;
  source?: EnrichmentSource;
  data_source?: DataSource;
  sort?: SortOrder;
}
