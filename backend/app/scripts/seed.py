"""Offline seed script — the ONLY place we bulk-enrich.

Generates 500+ companies, enriches + scores each, and upserts to Atlas so the
dashboard is full without hammering the live API.

Free-tier discipline (critical):
  - Gemini free tier is ~10-15 req/min and only a few hundred/day. So we live-
    enrich at most `--gemini-limit` accounts, sleeping `--delay` seconds between
    calls, and let the deterministic fallback enricher handle the rest. The
    moment Gemini errors/quota-outs, we stop calling it and finish on fallback.
  - This keeps the run fast, well under daily quota, and never blocks the book
    from being fully scored and persisted.

Usage:
  python -m app.scripts.seed                      # 500 accounts, ~25 via Gemini
  python -m app.scripts.seed --count 600 --gemini-limit 0   # all fallback (no API)
  python -m app.scripts.seed --gemini-limit 40 --delay 4.5
"""

import argparse
import asyncio

from app.core.logging import configure_logging, get_logger
from app.db.indexes import ensure_indexes
from app.db.mongo import close_client, get_db
from app.models.account import Account
from app.models.enrichment import EnrichmentSource
from app.models.icp import ICP
from app.repositories import accounts_repo
from app.scripts.generate_data import generate_companies
from app.services import gemini_client
from app.services.enrichment import enrich_company
from app.services.fallback_enricher import fallback_enrich
from app.services.scoring import score_account

logger = get_logger("seed")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed the accounts collection.")
    p.add_argument("--count", type=int, default=500, help="How many companies to generate.")
    p.add_argument(
        "--gemini-limit", type=int, default=25,
        help="Max accounts to live-enrich via Gemini; the rest use the fallback.",
    )
    p.add_argument(
        "--delay", type=float, default=4.0,
        help="Seconds to sleep between Gemini calls (rate-limit throttle).",
    )
    return p.parse_args()


async def run(count: int, gemini_limit: int, delay: float) -> None:
    settings_icp = ICP()  # default ICP (Phase 4 will allow editing it in Mongo)

    # Ensure indexes exist before bulk writes so the collection is query-ready.
    await ensure_indexes(get_db())

    companies = generate_companies(count)
    logger.info("Generated %d companies. Enriching + scoring…", len(companies))

    # Budget the LIVE work by attempts (not successes): a single transient parse
    # miss still consumes one attempt but doesn't abort the run. We only stop
    # early when the client disables itself on a fatal auth/model error.
    gemini_attempts = 0
    source_tally = {EnrichmentSource.GEMINI.value: 0, EnrichmentSource.FALLBACK.value: 0}

    for i, company in enumerate(companies, start=1):
        if gemini_attempts < gemini_limit and not gemini_client.is_disabled():
            enrichment = await enrich_company(company)  # tries Gemini, falls back internally
            gemini_attempts += 1
            if gemini_client.is_disabled():
                logger.warning("Gemini disabled (fatal); remaining accounts use fallback.")
            await asyncio.sleep(delay)  # throttle after any live attempt
        else:
            enrichment = fallback_enrich(company)

        source_tally[enrichment.source.value] += 1

        fit = score_account(company, enrichment, settings_icp)
        account = Account(
            _id=company.domain, company=company, enrichment=enrichment, fit=fit
        )
        await accounts_repo.upsert_account(account)

        if i % 50 == 0 or i == len(companies):
            logger.info("  …%d/%d upserted", i, len(companies))

    # ── Report ──
    total = await accounts_repo.count()
    tiers = await accounts_repo.tier_counts()
    logger.info("Seed complete.")
    logger.info("  Documents in collection : %d", total)
    logger.info("  Enrichment source       : gemini=%d, fallback=%d",
                source_tally["gemini"], source_tally["fallback"])
    logger.info("  Tier distribution       : Hot=%d, Warm=%d, Cold=%d",
                tiers.get("Hot", 0), tiers.get("Warm", 0), tiers.get("Cold", 0))


async def _main() -> None:
    configure_logging()
    args = _parse_args()
    try:
        await run(args.count, args.gemini_limit, args.delay)
    finally:
        await close_client()


if __name__ == "__main__":
    asyncio.run(_main())
