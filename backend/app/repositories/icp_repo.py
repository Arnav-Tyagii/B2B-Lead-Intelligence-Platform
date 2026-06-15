"""Repository for the ICP config document.

The ICP lives as a single document (`_id="icp"`) in a small `config` collection
so it can be edited at runtime (PUT /icp) and the scoring engine can read the
current targets/weights. When no document exists yet, we return the code
defaults from the ICP model — so the app works out of the box before any edit.
"""

from app.db.mongo import get_db
from app.models.icp import ICP

CONFIG_COLLECTION = "config"
ICP_DOC_ID = "icp"


def _collection():
    return get_db()[CONFIG_COLLECTION]


async def get_icp() -> ICP:
    doc = await _collection().find_one({"_id": ICP_DOC_ID})
    if not doc:
        return ICP()  # sensible defaults until one is saved
    doc.pop("_id", None)
    return ICP(**doc)


async def save_icp(icp: ICP) -> ICP:
    payload = {"_id": ICP_DOC_ID, **icp.model_dump()}
    await _collection().replace_one({"_id": ICP_DOC_ID}, payload, upsert=True)
    return icp
