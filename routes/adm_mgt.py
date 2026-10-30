from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.userM import UserModel
from services import adminService
from services.authService import require_roles

# Every route here is admin only.
router = APIRouter(
    prefix="/api/adm-mgt", tags=["Admin Management"], dependencies=[Depends(require_roles("admin"))]
)


def _payload(data, **kwargs) -> dict:
    return data.model_dump(**kwargs) if hasattr(data, "model_dump") else data.dict(**kwargs)


class UserUpdateSchema(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class AssignmentSchema(BaseModel):
    supervisor_id: int
    supervisee_id: int


class CriterionSchema(BaseModel):
    name: str
    description: Optional[str] = None
    max_marks: int = 10
    sort_order: int = 0
    is_active: bool = True


# --------------------------------------------------------------------- users
@router.get("/users")
def users(role: Optional[str] = None, q: Optional[str] = None, db: Session = Depends(get_db)):
    return {"status": "success", "data": adminService.list_users(db, role, q)}


@router.patch("/users/{user_id}")
def patch_user(
    user_id: int, data: UserUpdateSchema,
    admin: UserModel = Depends(require_roles("admin")), db: Session = Depends(get_db),
):
    return {"status": "success", "data": adminService.update_user(db, admin, user_id, data.role, data.is_active)}


# --------------------------------------------------------------- assignments
@router.get("/assignments")
def assignments(db: Session = Depends(get_db)):
    return {"status": "success", "data": adminService.list_assignments(db)}


@router.post("/assignments", status_code=status.HTTP_201_CREATED)
def add_assignment(data: AssignmentSchema, db: Session = Depends(get_db)):
    return {"status": "success", "data": adminService.create_assignment(db, data.supervisor_id, data.supervisee_id)}


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignment(assignment_id: int, db: Session = Depends(get_db)):
    adminService.delete_assignment(db, assignment_id)


# -------------------------------------------------------------------- rubric
@router.get("/criteria")
def criteria(db: Session = Depends(get_db)):
    return {"status": "success", "data": adminService.list_all_criteria(db)}


@router.post("/criteria", status_code=status.HTTP_201_CREATED)
def add_criterion(data: CriterionSchema, db: Session = Depends(get_db)):
    return {"status": "success", "data": adminService.create_criterion(db, _payload(data))}


@router.put("/criteria/{criterion_id}")
def edit_criterion(criterion_id: int, data: CriterionSchema, db: Session = Depends(get_db)):
    return {"status": "success", "data": adminService.update_criterion(db, criterion_id, _payload(data))}


@router.delete("/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_criterion(criterion_id: int, db: Session = Depends(get_db)):
    adminService.deactivate_criterion(db, criterion_id)


# ------------------------------------------------------------------- reports
@router.get("/reports/overview")
def reports_overview(db: Session = Depends(get_db)):
    return {"status": "success", "data": adminService.overview(db)}
