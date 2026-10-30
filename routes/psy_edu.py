from datetime import date
from typing import Optional

from pydantic import BaseModel

from models.psychoEducation import PsychoEducationModel
from routes.owned_router import build_owned_router


class PsychoEducationSchema(BaseModel):
    title: str
    topic: Optional[str] = None
    target_group: Optional[str] = None
    delivery_method: str = "Workshop"
    activity_date: date
    participant_count: int = 0
    materials_notes: Optional[str] = None
    outcome_notes: Optional[str] = None


router = build_owned_router(
    "/api/psy-edu", "Psychoeducation", PsychoEducationModel, PsychoEducationSchema, "activity_date"
)
