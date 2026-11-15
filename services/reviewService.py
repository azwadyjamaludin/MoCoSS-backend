"""One review flow for every reviewable module.

To make another module reviewable: add ReviewColumns to its model and add one entry to MODULES.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.caseAnal import CaseAnalysisModel
from models.logBook import LogBookModel
from models.review import ReviewModel
from models.supervisorAssignment import SupervisorAssignmentModel
from models.userM import UserModel
from services.serializeUtil import to_dict

EDITABLE_STATUSES = ("draft", "returned")
DECISIONS = ("approved", "returned")
STATUSES = ("draft", "submitted", "approved", "returned")


@dataclass(frozen=True)
class ReviewableModule:
    model: type
    editable: tuple                       # fields the counselor may write
    title: Callable[[object], str]
    subtitle: Callable[[object], str]


MODULES = {
    "log-book": ReviewableModule(
        LogBookModel,
        ("activity_title", "session_date", "duration_minutes", "category", "reflection_notes"),
        lambda r: r.activity_title,
        lambda r: f"{r.category or ''} · {r.session_date.isoformat() if r.session_date else ''}".strip(" ·"),
    ),
    "case-anal": ReviewableModule(
        CaseAnalysisModel,
        ("client_code", "presenting_problem", "session_dynamics", "sections"),
        lambda r: r.client_code,
        lambda r: (r.presenting_problem or "")[:90],
    ),
}


def get_module(name: str) -> ReviewableModule:
    module = MODULES.get(name)
    if module is None:
        raise HTTPException(status_code=404, detail="Unknown module.")
    return module


def _not_found():  # same answer for "missing" and "not yours", so ids cannot be probed
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")


def _own_view(record) -> dict:
    """What a counselor may see of their own record. Field supervisor advice is for the supervisor only."""
    data = to_dict(record)
    data.pop("field_advice", None)
    return data


def list_own(db: Session, module: str, user: UserModel) -> List[dict]:
    Model = get_module(module).model
    rows = db.query(Model).filter(Model.user_id == user.id).order_by(Model.id.desc()).all()
    return [_own_view(r) for r in rows]


def _own(db: Session, module: str, user: UserModel, record_id: int):
    Model = get_module(module).model
    record = db.get(Model, record_id)
    if record is None or record.user_id != user.id:
        raise _not_found()
    return record


def get_own(db: Session, module: str, user: UserModel, record_id: int) -> dict:
    return _own_view(_own(db, module, user, record_id))


def _apply(record, module: ReviewableModule, data: dict) -> None:
    for field in module.editable:
        if field in data:
            setattr(record, field, data[field])


def create_own(db: Session, module: str, user: UserModel, data: dict, submit: bool) -> dict:
    spec = get_module(module)
    record = spec.model(user_id=user.id, status="draft")
    _apply(record, spec, data)
    if submit:
        record.status, record.submitted_at = "submitted", datetime.utcnow()
    db.add(record)
    db.commit()
    db.refresh(record)
    return _own_view(record)


def update_own(db: Session, module: str, user: UserModel, record_id: int, data: dict, submit: bool) -> dict:
    spec = get_module(module)
    record = _own(db, module, user, record_id)
    if record.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=409, detail="This record was submitted and can no longer be edited.")
    _apply(record, spec, data)
    if submit:
        record.status, record.submitted_at = "submitted", datetime.utcnow()
    db.commit()
    db.refresh(record)
    return _own_view(record)


def submit_own(db: Session, module: str, user: UserModel, record_id: int) -> dict:
    record = _own(db, module, user, record_id)
    if record.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=409, detail="This record is already submitted.")
    record.status, record.submitted_at = "submitted", datetime.utcnow()
    db.commit()
    db.refresh(record)
    return _own_view(record)


def supervisee_ids(db: Session, supervisor: UserModel) -> List[int]:
    rows = db.query(SupervisorAssignmentModel.supervisee_id).filter(
        SupervisorAssignmentModel.supervisor_id == supervisor.id
    )
    return [r[0] for r in rows]


def _name(db: Session, user_id: Optional[int]) -> Optional[str]:
    user = db.get(UserModel, user_id) if user_id else None
    return (user.full_name or user.email) if user else None


def queue(db: Session, supervisor: UserModel, status_filter: str = "submitted", module: Optional[str] = None) -> List[dict]:
    """Records from the supervisor's own supervisees, across every reviewable module, oldest submission first."""
    if status_filter != "all" and status_filter not in STATUSES:
        raise HTTPException(status_code=422, detail="Unknown status.")
    if module is not None:
        get_module(module)
    ids = supervisee_ids(db, supervisor)
    if not ids:
        return []

    items = []
    for name, spec in MODULES.items():
        if module and module != name:
            continue
        Model = spec.model
        query = db.query(Model).filter(Model.user_id.in_(ids), Model.status != "draft")  # drafts are private
        if status_filter != "all":
            query = query.filter(Model.status == status_filter)
        for r in query.all():
            items.append({
                "module": name, "id": r.id, "title": spec.title(r), "subtitle": spec.subtitle(r),
                "status": r.status, "counselor_id": r.user_id, "counselor_name": _name(db, r.user_id),
                "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
                "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            })
    items.sort(key=lambda i: i["submitted_at"] or "")
    return items


def _reviewable(db: Session, supervisor: UserModel, module: str, record_id: int):
    Model = get_module(module).model
    record = db.get(Model, record_id)
    if record is None or record.status == "draft" or record.user_id not in supervisee_ids(db, supervisor):
        raise _not_found()
    return record


def get_for_review(db: Session, supervisor: UserModel, module: str, record_id: int) -> dict:
    record = _reviewable(db, supervisor, module, record_id)
    history = (
        db.query(ReviewModel).filter(ReviewModel.module == module, ReviewModel.record_id == record_id)
        .order_by(ReviewModel.id.desc()).all()
    )
    data = to_dict(record)
    data["module"] = module
    data["counselor_name"] = _name(db, record.user_id)
    data["reviewer_name"] = _name(db, record.reviewed_by)
    data["history"] = [
        {**to_dict(h), "reviewer_name": _name(db, h.reviewer_id)} for h in history
    ]
    return data


def decide(
    db: Session, supervisor: UserModel, module: str, record_id: int,
    decision: str, comment: Optional[str], field_advice: Optional[str],
) -> dict:
    if decision not in DECISIONS:
        raise HTTPException(status_code=422, detail="Decision must be approved or returned.")
    comment = (comment or "").strip() or None
    field_advice = (field_advice or "").strip() or None
    if decision == "returned" and not comment:
        raise HTTPException(status_code=422, detail="Say what the counselor should change when returning a record.")

    record = _reviewable(db, supervisor, module, record_id)
    if record.status != "submitted":
        raise HTTPException(status_code=409, detail="Only a submitted record can be reviewed.")

    now = datetime.utcnow()
    record.status, record.reviewed_at, record.reviewed_by = decision, now, supervisor.id
    record.review_comment, record.field_advice = comment, field_advice
    db.add(ReviewModel(
        module=module, record_id=record_id, reviewer_id=supervisor.id,
        decision=decision, comment=comment, field_advice=field_advice,
    ))
    db.commit()
    return get_for_review(db, supervisor, module, record_id)
