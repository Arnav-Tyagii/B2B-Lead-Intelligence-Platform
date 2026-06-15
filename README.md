# B2B Lead Intelligence Platform

An account-based go-to-market (GTM) intelligence tool in the spirit of Demandbase.
It acquires company firmographics, enriches each account with GenAI
(technographics, buying-intent signals, pain points, outreach), scores every
account against an Ideal Customer Profile (ICP), and presents a prioritized book
of business in an editorial **"Newsprint"** web app.

**Runs entirely on free tiers** (Vercel + Render + MongoDB Atlas M0 + Gemini free tier).

---

## Architecture

```
┌─────────────────────┐        HTTPS        ┌──────────────────────┐
│  Next.js (Vercel)   │  ───────────────►   │  FastAPI (Render)    │
│  App Router, TS     │   NEXT_PUBLIC_      │  api → services →    │
│  Newsprint UI       │   API_URL           │  repositories → models│
└─────────────────────┘                     └──────────┬───────────┘
                                                        │ Motor (pooled)
                                              ┌─────────▼──────────┐   ┌──────────────┐
                                              │ MongoDB Atlas (M0) │   │ Gemini API   │
                                              │ accounts, config   │   │ flash-lite   │
                                              └────────────────────┘   └──────────────┘
```

- **Clean layering** on the backend: routers are thin; logic lives in services;
  Mongo access is isolated in repositories; pydantic models are the typed contract.
- **Stateless backend** (all state in Mongo) so it scales horizontally.
- **Server-side pagination/filter/sort** on `/accounts` — never returns the whole collection.
- **Single pooled Motor client**; indexes on `fit.tier`, `fit.total`, `company.industry`, `company.country`.
- **Rate-limit-aware Gemini client** (backoff, concurrency cap, single-flight) with a
  **deterministic fallback enricher** and **fail-fast disable** on fatal errors.
- **TTL read caching** for `/stats` and account lists; **loading skeletons** everywhere
  for graceful cold starts.

```
/backend     FastAPI app, services, repositories, models, seed script, tests
/frontend    Next.js App Router, Newsprint design system, typed API client
```

---

## Tech stack

| Layer    | Tech |
|----------|------|
| Frontend | Next.js 14 (App Router), TypeScript (strict), Tailwind, recharts, react-fast-marquee, lucide-react, cva, tailwind-merge |
| Backend  | FastAPI (Python 3.11+), async, pydantic v2, pydantic-settings, motor, google-generativeai |
| Database | MongoDB Atlas (free M0) |
| GenAI    | Google Gemini `gemini-2.5-flash-lite` |
| Hosting  | Vercel (frontend), Render (backend) |

---

## Prerequisites

- **Python 3.11+** and **Node.js 18+**
- A **MongoDB Atlas** free (M0) cluster + connection string
- *(Optional)* a **Google Gemini API key** — without it, enrichment uses the
  deterministic fallback (the app still works fully)

---

## Local setup

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # then edit .env with your values
```

Fill `backend/.env`:

```ini
MONGODB_URI=mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=lead_intelligence
GEMINI_API_KEY=            # optional
GEMINI_MODEL=gemini-2.5-flash-lite
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
ENVIRONMENT=development
```

Seed the database (generates 500+ companies, enriches, scores, upserts):

```bash
# Default: ~25 live Gemini enrichments (throttled), the rest via fallback.
python -m app.scripts.seed

# Fully offline (no API calls) if you have no key / want speed:
python -m app.scripts.seed --gemini-limit 0
```

> **Free-tier note:** Gemini `flash-lite` allows only ~20 requests/day, so most
> seed records intentionally use the deterministic fallback. This is by design —
> the dashboard is fully populated and scored without depending on live quota.

#### Real data acquisition (SEC EDGAR + Greenhouse/Lever)

The seed pipeline is **source-agnostic**: acquisition sits behind one `Acquirer`
interface (`app/scripts/acquirers/`), so the same enrich → score → upsert flow
runs over either synthetic or real firmographics. Pick a source with `--source`:

```bash
# Real firmographics from SEC EDGAR + all free overlays, no Gemini. (--with-all =
# hiring intent + news/buzz + Wikidata). --reset all gives a pure real-data book.
python -m app.scripts.seed --source sec --with-all --reset all --gemini-limit 0

# Pick overlays individually instead of --with-all:
python -m app.scripts.seed --source sec --with-intent --with-news --with-wiki

# Also AI-enrich a handful within the daily Gemini quota:
python -m app.scripts.seed --source sec --with-all --gemini-limit 20
```

**Free data sources layered into the pipeline (all key-less APIs):**

| Source | Adds | Flag |
| --- | --- | --- |
| SEC EDGAR | revenue, industry (SIC), HQ/country, employees | `--source sec` |
| Greenhouse / Lever | live open-role count → hiring intent | `--with-intent` |
| Google News + Hacker News | real recent headlines + buzz volume → intent | `--with-news` |
| Wikidata | founding year + crisp company description | `--with-wiki` |
| Clearbit Logo API | real company logos in the UI (frontend, automatic) | — |

- **SEC EDGAR** (`data.sec.gov`) is a public JSON API — *API ingestion, not
  scraping*. No daily quota; it only asks for ≤10 req/s and a `User-Agent` with a
  contact (override via the `SEC_USER_AGENT` env var). It supplies revenue,
  industry (SIC), and HQ/country; ~110 well-known companies are curated in
  `seed_universe.py`. Acquiring 100–200 companies takes well under a minute.
- **Greenhouse/Lever** public board endpoints add open-roles as hiring-intent
  headlines (mined by the existing fallback enricher). Coverage is partial by
  design — only companies with a known public board are augmented.
- Real accounts are stamped `data_source="sec_edgar"`, surfaced with a **SEC**
  badge, a **Data Source** filter, and the default **Real Data First** sort.
- Only the **Gemini AI layer** is daily-rate-limited; acquisition + scoring of all
  companies is unlimited and re-runnable any day (`upsert` accumulates).
- The synthetic generator remains the default (`--source synthetic`), so the
  existing offline path is unchanged.

Run the API:

```bash
uvicorn app.main:app --reload
# → http://localhost:8000   (docs at /docs, health at /health)
```

Run the tests:

```bash
pytest
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
# → http://localhost:3000
```

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/health` | Liveness (also the keep-warm target) |
| GET  | `/accounts` | Paginated/filtered/sorted list — `page, page_size (≤100), tier, industry, country, min_score, sort` |
| GET  | `/accounts/{domain}` | Full account by domain |
| POST | `/enrich` | On-demand single enrich + score + upsert (rate-limit aware) |
| GET  | `/stats` | Totals, tier distribution, top industries, average score (cached) |
| GET/PUT | `/icp` | Read / update the ICP config (weights must sum to 100) |

---

## Deployment

### A. MongoDB Atlas
1. Create a free **M0** cluster.
2. Add a database user and allow network access (`0.0.0.0/0` for the demo, or
   Render's egress IPs).
3. Copy the SRV connection string → used as `MONGODB_URI`.
4. Seed it once from your machine (`python -m app.scripts.seed`), pointing
   `.env` at the Atlas URI.

### B. Backend → Render (free web service)
This repo includes **`render.yaml`** (a Blueprint). Either import the repo as a
Blueprint, or create a Web Service manually with:

- **Root directory:** `backend`
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health check path:** `/health`
- **Environment variables:**
  - `MONGODB_URI` (secret), `MONGODB_DB_NAME=lead_intelligence`
  - `GEMINI_API_KEY` (secret, optional), `GEMINI_MODEL=gemini-2.5-flash-lite`
  - `CORS_ORIGINS=https://your-app.vercel.app`  ← your Vercel URL
  - `PYTHON_VERSION=3.11.9`

### C. Frontend → Vercel
- **Root directory:** `frontend`
- Vercel auto-detects Next.js (build `next build`, no extra config).
- **Environment variable:** `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`
- Redeploy after setting it (it's inlined at build time).

### D. Wire CORS + warm-up
- Set the backend's `CORS_ORIGINS` to the exact Vercel origin (no trailing slash).
- The frontend pings `/health` on first load to wake the backend.

---

## Free-tier guardrails (baked in)

- **Gemini** (~10–15 req/min, ~few hundred/day): bulk enrichment only via the
  throttled seed script; live enrichment is one account on demand; exponential
  backoff on 429; deterministic fallback; fail-fast disable on fatal errors.
- **Atlas M0** (512 MB, few connections): single pooled Motor client, lean
  documents, indexes for all filter/sort fields.
- **Render free** (sleeps after ~15 min, ~50s cold start): `/health` endpoint +
  frontend warm-up + Newsprint loading skeletons everywhere. **Keep-warm:** point
  a free cron pinger (e.g. cron-job.org / UptimeRobot) at
  `https://your-backend.onrender.com/health` every ~10 minutes.
- **Vercel:** static-first frontend; data fetched client-side so cold starts show
  skeletons rather than a blank hang.

---

## Design system

The entire frontend follows the **Newsprint** system in `DESIGN_SYSTEM.md`:
zero border radius, visible grid borders, massive serif headlines, drop caps, a
marquee ticker, one inverted black section, grayscale halftone images, uppercase
mono labels, and hard-offset shadow hovers — responsive and accessible.

## Secrets

Never commit secrets. `.env` files are git-ignored; `.env.example` files document
every variable for both apps.
