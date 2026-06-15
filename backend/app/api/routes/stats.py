"""Stats router — dashboard KPIs and chart data. Cached in the service layer."""

from fastapi import APIRouter

from app.models.api import Stats
from app.services import stats_service

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=Stats)
async def get_stats() -> Stats:
    return await stats_service.get_stats()
