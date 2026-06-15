"""The Account aggregate — the persisted document and the primary API entity.

In MongoDB the document `_id` IS the company domain (unique, natural key). We
expose it on the model as `domain` via the `_id` alias so:
  - reading from Mongo: `Account(**doc)` maps `_id` → `domain`
  - writing to Mongo: `model_dump(by_alias=True)` maps `domain` → `_id`
This avoids storing the domain twice.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.models.company import Company
from app.models.enrichment import Enrichment
from app.models.fit import Fit


class Account(BaseModel):
    # populate_by_name lets us construct with either `domain=` or `_id=`.
    model_config = ConfigDict(populate_by_name=True)

    domain: str = Field(alias="_id", description="Company domain; the Mongo _id.")
    company: Company
    enrichment: Enrichment
    fit: Fit
