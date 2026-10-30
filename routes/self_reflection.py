from datetime import date
from typing import Optional

from pydantic import BaseModel

from models.selfReflection import SelfReflectionModel
from routes.owned_router import build_owned_router


class SelfReflectionSchema(BaseModel):
    title: str
    reflection_date: date
    content: str
    strengths: Optional[str] = None
    growth_areas: Optional[str] = None
    action_plan: Optional[str] = None


router = build_owned_router(
    "/api/reflect", "Self Reflection", SelfReflectionModel, SelfReflectionSchema, "reflection_date"
)
