"""Live enrich router — "Stop the Press".

POST /enrich performs ONE on-demand Gemini enrichment + score for a single
account and upserts it. Rate-limit aware via the Gemini client; degrades to the
deterministic fallback automatically (the response's `enrichment.source` tells
the UI which path produced it, so it can show a friendly fallback notice).
"""

from fastapi import APIRouter

from app.models.account import Account
from app.models.api import EnrichRequest
from app.services import accounts_service

router = APIRouter(tags=["enrich"])


@router.post("/enrich", response_model=Account, response_model_by_alias=False)
async def enrich(req: EnrichRequest) -> Account:
    return await accounts_service.enrich_and_store(req)
