from datetime import date
from typing import Optional

from pydantic import BaseModel

from models.profDev import ProfDevModel
from routes.owned_router import build_owned_router


class ProfDevSchema(BaseModel):
    activity_title: str
    activity_type: str = "Workshop"
    provider: Optional[str] = None
    activity_date: date
    hours: float = 0
    certificate_ref: Optional[str] = None
    learning_outcome: Optional[str] = None


router = build_owned_router(
    "/api/prof-dev", "Professional Development", ProfDevModel, ProfDevSchema, "activity_date"
)
