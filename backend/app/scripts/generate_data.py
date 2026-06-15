"""Synthetic company generator.

Produces 500+ realistic, varied companies for seeding. Design choices:
  - **Reproducible**: a fixed RNG seed means the same book every run, so the
    dashboard is stable and the data is testable.
  - **Realistic correlations**: revenue is derived from headcount via a
    per-employee revenue multiplier, not picked independently.
  - **Variety on purpose**: a mix of target and non-target industries/countries
    and sizes so the scored book spans Hot / Warm / Cold tiers.
  - **Unique domains**: the domain is the account `_id`, so we de-duplicate.

This module only builds `Company` objects; enrichment + scoring + persistence
happen in the Phase 3 seed script.
"""

import random

from app.models.company import Company

# Mix of ICP-target verticals and a few off-ICP ones to create Cold accounts.
_INDUSTRIES = [
    "SaaS", "FinTech", "Cybersecurity", "MarTech", "Cloud Infrastructure",
    "E-commerce", "HR Tech", "Data & Analytics",  # target verticals
    "Manufacturing", "Healthcare", "Retail", "Logistics",  # off-ICP
]

# Countries: target markets plus a few outside to vary geography scoring.
_COUNTRIES: list[tuple[str, list[str]]] = [
    ("United States", ["San Francisco, CA", "New York, NY", "Austin, TX", "Boston, MA", "Seattle, WA"]),
    ("United Kingdom", ["London", "Manchester", "Bristol"]),
    ("Canada", ["Toronto", "Vancouver", "Montreal"]),
    ("India", ["Bengaluru", "Mumbai", "Hyderabad"]),
    ("Germany", ["Berlin", "Munich", "Hamburg"]),
    ("Australia", ["Sydney", "Melbourne"]),       # off-ICP geography
    ("Singapore", ["Singapore"]),                  # off-ICP geography
    ("Brazil", ["São Paulo"]),                     # off-ICP geography
]

_NAME_PREFIXES = [
    "Aero", "Bright", "Cloud", "Data", "Echo", "Flux", "Giga", "Hyper", "Iron",
    "Lumen", "Nova", "Orbit", "Pulse", "Quanta", "Rapid", "Stack", "True",
    "Vertex", "Wave", "Zenith", "Apex", "Core", "Delta", "North", "Summit",
]
_NAME_SUFFIXES = [
    "Labs", "Works", "Systems", "Logic", "Sphere", "Base", "Scale", "Flow",
    "Grid", "Mind", "Sync", "Forge", "Stream", "Hub", "Point", "Sense",
]
_TLDS = ["com", "io", "ai", "co", "tech"]

# News templates keyed to keywords the fallback enricher / intent scorer detect.
_NEWS_TEMPLATES = [
    "{name} raised a ${amt}M Series {series} funding round.",
    "{name} announces plans to hire {n} engineers this year.",
    "{name} launches a new AI-powered product line.",
    "{name} unveils a strategic partnership with a major cloud provider.",
    "{name} expands operations with a new international office.",
    "{name} acquires a smaller competitor to broaden its platform.",
    "{name} reports record quarterly growth in active customers.",
    "{name} introduces an integration marketplace for developers.",
]


def _make_domain(name: str, rng: random.Random, used: set[str]) -> str:
    base = name.lower().replace(" ", "")
    domain = f"{base}.{rng.choice(_TLDS)}"
    # Guarantee uniqueness (domain is the Mongo _id).
    suffix = 1
    while domain in used:
        suffix += 1
        domain = f"{base}{suffix}.{rng.choice(_TLDS)}"
    used.add(domain)
    return domain


def _make_news(name: str, rng: random.Random) -> list[str]:
    count = rng.choice([1, 1, 2])  # mostly one, sometimes two
    items = rng.sample(_NEWS_TEMPLATES, count)
    return [
        item.format(
            name=name,
            amt=rng.choice([8, 12, 20, 35, 50, 80, 120]),
            series=rng.choice(["A", "B", "C", "D"]),
            n=rng.choice([25, 50, 100, 200]),
        )
        for item in items
    ]


def generate_companies(count: int = 500, seed: int = 42) -> list[Company]:
    rng = random.Random(seed)
    used_domains: set[str] = set()
    companies: list[Company] = []

    for _ in range(count):
        name = f"{rng.choice(_NAME_PREFIXES)}{rng.choice(_NAME_SUFFIXES)}"
        domain = _make_domain(name, rng, used_domains)
        industry = rng.choice(_INDUSTRIES)
        country, cities = rng.choice(_COUNTRIES)
        hq = rng.choice(cities)

        # Headcount across a wide log-ish spread (50 → 12,000) for tier variety.
        employees = rng.choice(
            [50, 80, 120, 180, 250, 400, 650, 900, 1500, 2500, 4000, 5500, 8000, 12000]
        )
        # Revenue correlated to headcount: $80k–$320k per employee.
        rev_per_head = rng.randint(80_000, 320_000)
        revenue = employees * rev_per_head

        founded = rng.randint(1995, 2022)
        description = (
            f"{name} is a {industry} company headquartered in {hq}, building "
            f"products for modern teams. With roughly {employees:,} employees, it "
            f"serves customers across {country} and beyond."
        )

        companies.append(
            Company(
                name=name,
                domain=domain,
                industry=industry,
                employee_count=employees,
                estimated_revenue_usd=revenue,
                hq_location=hq,
                country=country,
                founded_year=founded,
                description=description,
                recent_news=_make_news(name, rng),
            )
        )

    return companies


if __name__ == "__main__":
    sample = generate_companies()
    print(f"Generated {len(sample)} companies (unique domains: "
          f"{len({c.domain for c in sample})}).")
    print("Example:", sample[0].model_dump())
