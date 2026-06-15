"""ICP config router (optional feature).

GET returns the current ICP (targets + weights); PUT validates and persists a
new one. Weight-sum validation is enforced by the ICP model, so an invalid
payload returns 422 automatically. Re-scoring the existing book against a new
ICP is intentionally left to an explicit action (not done here) to avoid an
accidental 500-account rewrite on every edit.
"""

from fastapi import APIRouter

from app.models.icp import ICP
from app.repositories import icp_repo
from app.services import stats_service

router = APIRouter(tags=["icp"])


@router.get("/icp", response_model=ICP)
async def get_icp() -> ICP:
    return await icp_repo.get_icp()


@router.put("/icp", response_model=ICP)
async def update_icp(icp: ICP) -> ICP:
    saved = await icp_repo.save_icp(icp)
    stats_service.invalidate()
    return saved
