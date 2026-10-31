from datetime import date
from typing import Optional

from pydantic import BaseModel

from models.psychologyTest import PsychologyTestModel
from routes.owned_router import build_owned_router


class PsychologyTestSchema(BaseModel):
    test_name: str
    case_ref: Optional[str] = None  # de-identified code only, never a client name
    test_date: date
    raw_score: Optional[float] = None
    interpretation: Optional[str] = None
    notes: Optional[str] = None


router = build_owned_router(
    "/api/psy-test", "Psychology Test", PsychologyTestModel, PsychologyTestSchema, "test_date"
)
