# Build Spec: B2B Lead Intelligence Platform (full-stack, scalable, free-tier)

You are building, from scratch, a production-minded **B2B Lead Intelligence Platform** — an account-based go-to-market (GTM) intelligence tool in the spirit of Demandbase. It acquires company firmographics, enriches each account with GenAI (technographics, buying-intent signals, pain points, outreach), scores every account against an Ideal Customer Profile (ICP), and presents a prioritized book of business in a beautiful editorial web app.

**Before writing any code, read `DESIGN_SYSTEM.md` in this repo fully — the entire frontend must follow that "Newsprint" design system.** Then propose a plan and wait for my confirmation before scaffolding.

This must run **entirely on free tiers**. Encode the free-tier guardrails below; do not assume any paid capacity.

---

## Tech stack (use exactly this)

- **Frontend:** Next.js 14+ (App Router) · TypeScript (strict) · Tailwind CSS · `lucide-react` · `class-variance-authority` · `tailwind-merge` · `recharts` (charts) · `react-fast-marquee` (ticker). Deploy target: **Vercel**.
- **Backend:** **FastAPI** (Python 3.11+) · async · `pydantic` v2 / `pydantic-settings` · `motor` (async MongoDB) · `google-generativeai`. Deploy target: **Render** (free web service).
- **Database:** **MongoDB Atlas** (free M0 cluster).
- **GenAI:** Google Gemini, model **`gemini-2.5-flash-lite`** (free tier; cheap, ideal for structured extraction).
- **Tooling:** `npm` (frontend); `venv` + `pip` (backend). Repo is a monorepo: `/frontend` and `/backend`.

---

## Architecture principles (this is the "highly scalable" part — follow strictly)

1. **Clean layering** in the backend: `api/` (routers, thin) → `services/` (business logic) → `repositories/` (Mongo access) → `models/` (pydantic schemas). No business logic in route handlers.
2. **Stateless backend** so it scales horizontally. All state in MongoDB.
3. **Repository pattern** over MongoDB. Create indexes on `fit.tier`, `fit.total`, `company.industry`, `company.country`.
4. **Server-side pagination, filtering, and sorting** on the accounts endpoint. Never return the whole collection. Default page size 20, max 100.
5. **Read caching:** lightweight TTL cache for `/stats` and list reads; use Next.js fetch caching on the frontend.
6. **Rate-limit-aware Gemini client:** exponential backoff on HTTP 429, a concurrency cap, and single-flight. **Never batch-enrich hundreds of accounts live.** Bulk enrichment happens only in the offline seed script, throttled.
7. **Pluggable enrichment with graceful degradation:** if the API key is missing, the call fails, or we're rate-limited, fall back to a deterministic heuristic enricher (seeded by domain so output is stable). On a fatal auth/model error, disable Gemini for the rest of the process and log one clear message — do not retry it for every record.
8. **Config via environment variables only** (`pydantic-settings`). No secrets in code. Provide `.env.example` for both apps. Add `.gitignore`.
9. **Typed contract:** define pydantic schemas on the backend and matching TypeScript types on the frontend so the API shape is shared and type-safe.
10. **Observability:** structured logging, a `GET /health` endpoint, and CORS locked to the Vercel frontend origin (configurable via env).
11. **Tests:** unit tests for the scoring engine and the enrichment fallback at minimum.

---

## Free-tier guardrails (critical — bake these into the design)

- **Gemini free tier** allows roughly 10–15 requests/min and a few hundred/day. Therefore: seed the database via a **throttled offline script** (sleep between calls, backoff on 429); live enrichment is **one account on demand only**. If quota is exhausted, fall back gracefully and surface a friendly notice in the UI.
- **MongoDB Atlas M0** is 512 MB with limited connections. Use a **single pooled Motor client** (module-level), keep documents lean, and rely on indexes.
- **Render free web service** sleeps after ~15 min idle and cold-starts in ~50s. Add `GET /health`, document a free keep-warm pinger (e.g. a free cron service hitting `/health`), make the frontend **warm the backend on first load**, and show **Newsprint-styled loading skeletons** everywhere so a cold start never looks broken.
- **Vercel** hosts the frontend (and any light serverless routes). Keep serverless functions fast.

---

## Domain spec (build exactly this)

### Data model — MongoDB `accounts` collection
- `_id` = company domain (unique).
- `company`: `name, domain, industry, employee_count, estimated_revenue_usd, hq_location, country, founded_year, description, recent_news[]`
- `enrichment`: `technographics[], intent_signals[], intent_topics[], pain_points[], outreach_email, gtm_recommendation, source ("gemini"|"fallback")`
- `fit`: `total (0-100), tier ("Hot"|"Warm"|"Cold"), breakdown{industry, company_size, revenue, geography, technographics, intent}, rationale`

### ICP + scoring engine (must be transparent — always return the breakdown)
Weights (sum to 100): **industry 25, company_size 20, revenue 15, geography 10, technographics 15, intent 15.**
ICP:
- target_industries: SaaS, FinTech, Cybersecurity, MarTech, Cloud Infrastructure, E-commerce, HR Tech, Data & Analytics
- employees: 200–5000 (full points in band, half points within 2×)
- revenue: $20M–$2B (same partial-credit rule)
- target_countries: United States, United Kingdom, Canada, India, Germany
- target_technographics: Salesforce, HubSpot, Marketo, Snowflake, Segment, Outreach, Salesloft, Gong, 6sense, Clearbit
- intent: more distinct concrete signals → more points
Tiers: `total >= 70` → Hot, `>= 45` → Warm, else Cold.

### Enrichment
Prompt Gemini to return **strict minified JSON** with exactly the `enrichment` fields above (cap array lengths and email/recommendation length to control tokens/latency). Parse defensively (strip code fences, extract the JSON object). Deterministic fallback enricher produces plausible technographics (by industry), intent signals (inferred from `recent_news` keywords like funding/hiring/launch), topics, pain points, a templated personalized outreach email, and a GTM recommendation.

### Seed data
Generate **500+ realistic companies** (varied industries, employee sizes, revenue correlated to headcount, mixed geographies, 1–2 recent-news snippets each). The throttled seed script enriches + scores all of them and upserts to Atlas, so the dashboard is full without live rate-limit issues.

---

## Pages & features (apply the Newsprint design system rigorously)

1. **Dashboard — "The Front Page":** masthead header (`Vol. 1 | <today's date> | New York Edition`), KPI stats (total accounts, Hot count, average fit score), a **marquee ticker** of top Hot accounts/stats (black bg, white text, red accent badges), a tier-distribution chart and a top-industries chart, ornamental `✧ ✧ ✧` dividers, dot-grid background texture.
2. **Accounts — "The Index":** server-paginated, server-filtered newspaper-grid of accounts showing company, score (with a transparent indicator), tier badge, key firmographics. Filters: tier, industry, country, minimum score. Sort by score. Collapsed grid borders, uppercase mono column labels.
3. **Account detail — "The Feature Story":** giant serif headline (company name), **drop-cap** intro paragraph (description), firmographics block, technographics, intent signals, pain points, a **transparent score breakdown** bar, the AI **outreach email** in a bordered block, and the GTM recommendation — laid out like an editorial article with bylines, edition metadata, and a `Fig. 1.1` style caption on the placeholder image (grayscale, halftone dot texture).
4. **Live enrich — "Stop the Press":** input a company profile/domain → on-demand single Gemini enrich + score → render the result. Rate-limit aware, with a loading state and a graceful fallback notice.
5. **ICP settings (optional, if time):** view/edit ICP targets + weights and re-score the book.

Mandatory bold design choices from `DESIGN_SYSTEM.md`: zero border radius everywhere, visible vertical grid dividers, at least one **inverted (black) section** with red numbered accents, grayscale images, justified multi-column body text, hard-offset shadow hovers, uppercase `tracking-widest` mono labels. Fully **responsive** (single-column on mobile, drop `border-r`, scale headlines) and **accessible** (semantic HTML, `:focus-visible` rings, ARIA labels on icon buttons, alt text, 44px touch targets).

---

## Backend endpoints
- `GET /health` — liveness (also used to keep-warm).
- `GET /accounts` — query params: `page, page_size, tier, industry, country, min_score, sort` → paginated result with total count. Cached briefly.
- `GET /accounts/{domain}` — full account.
- `POST /enrich` — body: a company profile (or domain) → enrich + score one account, upsert, return it. Rate-limit aware.
- `GET /stats` — totals, tier distribution, industry distribution, avg score. Cached.
- `GET /icp` / `PUT /icp` — read/update ICP config (optional).

---

## Build in phases — do these IN ORDER and verify each before continuing

- **Phase 0 — Plan:** read `DESIGN_SYSTEM.md`; propose the monorepo folder structure for `/frontend` and `/backend` and the file list per layer. **Wait for my OK.**
- **Phase 1 — Backend scaffold:** FastAPI app, settings, pooled Mongo client + index creation on startup, `/health`, pydantic models/schemas.
- **Phase 2 — Domain services:** scoring engine, enrichment (Gemini + fallback + fail-fast disable), data generator; unit tests passing.
- **Phase 3 — Seed script:** generate 500+, throttled enrich, score, upsert to Atlas; run it and report tier counts.
- **Phase 4 — API:** the endpoints above with pagination/filtering/sorting, CORS, error handling, caching.
- **Phase 5 — Frontend scaffold:** Next.js + Tailwind configured with Newsprint tokens (colors, fonts via `@import`, textures, `.sharp-corners`, `.hard-shadow-hover`), and shared UI primitives (Button, Card, Badge, StatTicker, SectionLabel, LoadingSkeleton) built with `cva` + `tailwind-merge`.
- **Phase 6 — Pages:** dashboard, accounts (filters + pagination), account detail, live enrich — wired to the backend through a single typed API client, with loading skeletons and error states.
- **Phase 7 — Polish:** responsive pass, accessibility pass, micro-interactions, empty/error states, backend warm-up on first load.
- **Phase 8 — Deploy:** `.env.example` for both apps (no secrets committed), a thorough `README.md` covering local setup and deployment to Vercel (frontend) + Render (backend) + Atlas, including CORS origin and `NEXT_PUBLIC_API_URL` wiring and a keep-warm note.

---

## Working agreement (for you, Claude Code)
- After each phase, **run the app/tests and report status** before moving on. Ask before any destructive action.
- **Never commit secrets.** Use `.env` + `.gitignore`; provide `.env.example`.
- Keep functions small and **comment the "why"** — I will explain this code in an interview.
- Prefer clarity over cleverness; write idiomatic Next.js and FastAPI.
- Respect every free-tier guardrail above (pagination, backoff, single client, fallback).

## Acceptance criteria
- Locally: backend runs under `uvicorn`, frontend under `npm run dev`; the dashboard loads seeded accounts from Atlas.
- Accounts list filters/sorts/paginates **server-side**.
- Live enrich performs a single Gemini call on demand and degrades gracefully.
- The Newsprint design system is faithfully applied, responsive, and accessible.
- Both apps deploy on free tiers with documented, reproducible steps.
