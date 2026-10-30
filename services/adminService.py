from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.caseAnal import CaseAnalysisModel
from models.evaluation import EvaluationCriterionModel, EvaluationModel
from models.logBook import LogBookModel
from models.profDev import ProfDevModel
from models.psychoEducation import PsychoEducationModel
from models.refCons import ReferralConsultationModel
from models.selfReflection import SelfReflectionModel
from models.supervisorAssignment import SupervisorAssignmentModel
from models.userM import UserModel
from services.authService import SUPERVISOR_ROLES
from services.serializeUtil import to_dict

VALID_ROLES = ("admin", "supervisor", "field supervisor", "counselor")


def _user_view(u: UserModel) -> dict:
    return {
        "id": u.id, "email": u.email, "username": u.username, "full_name": u.full_name,
        "role": u.role, "is_active": bool(u.is_active), "is_mydid": bool(u.is_mydid),
    }


# --------------------------------------------------------------------- users
def list_users(db: Session, role: Optional[str] = None, q: Optional[str] = None):
    query = db.query(UserModel)
    if role:
        query = query.filter(UserModel.role == role)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter((UserModel.full_name.like(like)) | (UserModel.email.like(like)))
    return [_user_view(u) for u in query.order_by(UserModel.full_name, UserModel.id).all()]


def update_user(db: Session, admin: UserModel, user_id: int, role: Optional[str], is_active: Optional[bool]):
    user = db.get(UserModel, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.id == admin.id and (
        (role is not None and role != "admin") or is_active is False
    ):
        raise HTTPException(status_code=400, detail="You cannot demote or deactivate your own account.")
    if role is not None:
        if role not in VALID_ROLES:
            raise HTTPException(status_code=422, detail=f"Role must be one of: {', '.join(VALID_ROLES)}.")
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    db.commit()
    db.refresh(user)
    return _user_view(user)


# --------------------------------------------------------------- assignments
def _assignment_view(db: Session, a: SupervisorAssignmentModel) -> dict:
    supervisor = db.get(UserModel, a.supervisor_id)
    supervisee = db.get(UserModel, a.supervisee_id)
    return {
        "id": a.id,
        "supervisor_id": a.supervisor_id,
        "supervisor_name": supervisor.full_name if supervisor else None,
        "supervisee_id": a.supervisee_id,
        "supervisee_name": supervisee.full_name if supervisee else None,
    }


def list_assignments(db: Session):
    return [_assignment_view(db, a) for a in db.query(SupervisorAssignmentModel).order_by(SupervisorAssignmentModel.id)]


def create_assignment(db: Session, supervisor_id: int, supervisee_id: int):
    supervisor = db.get(UserModel, supervisor_id)
    supervisee = db.get(UserModel, supervisee_id)
    if supervisor is None or supervisor.role not in SUPERVISOR_ROLES:
        raise HTTPException(status_code=422, detail="supervisor_id must be a supervisor or field supervisor.")
    if supervisee is None or supervisee.role != "counselor":
        raise HTTPException(status_code=422, detail="supervisee_id must be a counselor.")
    assignment = SupervisorAssignmentModel(supervisor_id=supervisor_id, supervisee_id=supervisee_id)
    db.add(assignment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This assignment already exists.")
    db.refresh(assignment)
    return _assignment_view(db, assignment)


def delete_assignment(db: Session, assignment_id: int) -> None:
    assignment = db.get(SupervisorAssignmentModel, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    db.delete(assignment)
    db.commit()


# -------------------------------------------------------------------- rubric
def list_all_criteria(db: Session):
    rows = db.query(EvaluationCriterionModel).order_by(EvaluationCriterionModel.sort_order, EvaluationCriterionModel.id)
    return [to_dict(c) for c in rows]


def create_criterion(db: Session, data: dict):
    criterion = EvaluationCriterionModel(**data)
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    return to_dict(criterion)


def update_criterion(db: Session, criterion_id: int, data: dict):
    criterion = db.get(EvaluationCriterionModel, criterion_id)
    if criterion is None:
        raise HTTPException(status_code=404, detail="Criterion not found.")
    for key, value in data.items():
        setattr(criterion, key, value)
    db.commit()
    db.refresh(criterion)
    return to_dict(criterion)


def deactivate_criterion(db: Session, criterion_id: int) -> None:
    """Soft delete: old evaluations keep pointing at the criterion they were scored on."""
    criterion = db.get(EvaluationCriterionModel, criterion_id)
    if criterion is None:
        raise HTTPException(status_code=404, detail="Criterion not found.")
    criterion.is_active = False
    db.commit()


# ------------------------------------------------------------------- reports
def _count_by_user(db: Session, model, user_col):
    return dict(db.query(user_col, func.count(model.id)).group_by(user_col).all())


def overview(db: Session) -> dict:
    users = db.query(UserModel).all()
    by_role = {}
    for u in users:
        by_role[u.role] = by_role.get(u.role, 0) + 1

    log_minutes = dict(
        db.query(LogBookModel.user_id, func.coalesce(func.sum(LogBookModel.duration_minutes), 0))
        .group_by(LogBookModel.user_id).all()
    )
    cases = _count_by_user(db, CaseAnalysisModel, CaseAnalysisModel.user_id)
    referrals = _count_by_user(db, ReferralConsultationModel, ReferralConsultationModel.user_id)
    reflections = _count_by_user(db, SelfReflectionModel, SelfReflectionModel.user_id)
    psy_edu = _count_by_user(db, PsychoEducationModel, PsychoEducationModel.user_id)
    prof_dev = _count_by_user(db, ProfDevModel, ProfDevModel.user_id)
    pending_referrals = (
        db.query(func.count(ReferralConsultationModel.id))
        .filter(ReferralConsultationModel.status == "Pending").scalar() or 0
    )

    evaluations = db.query(EvaluationModel).all()
    percent_by_user = {}
    for e in evaluations:
        if e.max_total:
            percent_by_user.setdefault(e.supervisee_id, []).append(float(e.total_marks) / float(e.max_total) * 100)

    counselors = []
    for u in users:
        if u.role != "counselor":
            continue
        marks = percent_by_user.get(u.id, [])
        counselors.append({
            "id": u.id,
            "full_name": u.full_name,
            "log_hours": round(float(log_minutes.get(u.id, 0)) / 60, 1),
            "case_analyses": cases.get(u.id, 0),
            "referrals": referrals.get(u.id, 0),
            "reflections": reflections.get(u.id, 0),
            "psychoeducation": psy_edu.get(u.id, 0),
            "professional_development": prof_dev.get(u.id, 0),
            "latest_mark_percent": round(marks[-1], 1) if marks else None,
        })

    all_percent = [p for values in percent_by_user.values() for p in values]
    return {
        "users_total": len(users),
        "users_active": sum(1 for u in users if u.is_active),
        "users_by_role": by_role,
        "log_hours_total": round(sum(float(v) for v in log_minutes.values()) / 60, 1),
        "case_analyses_total": sum(cases.values()),
        "referrals_pending": pending_referrals,
        "evaluations_total": len(evaluations),
        "evaluation_average_percent": round(sum(all_percent) / len(all_percent), 1) if all_percent else None,
        "counselors": counselors,
    }
