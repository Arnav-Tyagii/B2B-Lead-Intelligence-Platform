# B2B Lead Intelligence Platform

Account-based GTM intelligence tool (Demandbase-style): acquire firmographics →
enrich with GenAI → score against an Ideal Customer Profile → present a
prioritized book of accounts in an editorial web app. Must run entirely on free tiers.

## How to work on this project
- The full, authoritative build plan lives in **`BUILD_SPEC.md`**. Follow its phases
  IN ORDER. After each phase, run the app/tests, report status, and wait for my
  approval before continuing. Ask before any destructive action.
- Before writing or editing ANY frontend/UI code, read **`DESIGN_SYSTEM.md`** and
  follow that "Newsprint" design system exactly (fonts, zero border radius, visible
  grid borders, drop caps, marquee ticker, one inverted black section, grayscale
  images, uppercase mono labels, hard-offset shadow hovers). Responsive + accessible.

## Stack (do not substitute)
- Frontend: Next.js (App Router) + TypeScript (strict) + Tailwind, on Vercel.
- Backend: FastAPI (Python 3.11+), async, pydantic v2, motor, on Render.
- DB: MongoDB Atlas (free M0). GenAI: Gemini `gemini-2.5-flash-lite`.
- Monorepo: `/frontend` and `/backend`.

## Hard rules (always apply)
- Clean layering on the backend: api → services → repositories → models. No logic in routers.
- Accounts endpoint MUST paginate + filter + sort server-side. Never return the whole collection.
- Single pooled Mongo client (module-level). Index tier, fit.total, industry, country.
- Gemini client: exponential backoff on 429, concurrency cap, deterministic fallback
  enricher when key missing / call fails / rate-limited. On a fatal auth/model error,
  disable Gemini for the rest of the process and log ONCE — never retry per record.
- NEVER batch-enrich hundreds of accounts live (free quota). Bulk enrichment is the
  throttled offline seed script only; live enrichment is one account on demand.
- Config via env vars only. NEVER commit secrets. Provide `.env.example`; add `.gitignore`.
- Comment the "why" — this code gets explained in an interview. Clarity over cleverness.

## Commands
- Backend dev:    cd backend && uvicorn app.main:app --reload   (http://localhost:8000, docs at /docs)
- Backend tests:  cd backend && pytest
- Seed DB:        cd backend && python -m app.scripts.seed        (add --gemini-limit 0 for fully offline)
- Generate only:  cd backend && python -m app.scripts.generate_data
- Frontend dev:   cd frontend && npm run dev                      (http://localhost:3000)
- Frontend build: cd frontend && npm run build
- Type-check FE:  cd frontend && npm run typecheck

Setup notes:
- Backend venv: cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
- Copy backend/.env.example → backend/.env ; copy frontend/.env.example → frontend/.env.local
