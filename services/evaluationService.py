from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.evaluation import EvaluationCriterionModel, EvaluationModel, EvaluationScoreModel
from models.supervisorAssignment import SupervisorAssignmentModel
from models.userM import UserModel
from services.authService import SUPERVISOR_ROLES
from services.serializeUtil import to_dict

SUPERVISEE_ROLE = "counselor"

# Used only when the rubric table is empty. Admins can change it in Admin Management.
DEFAULT_CRITERIA = [
    ("Counseling skills", "Rapport, listening, probing and use of techniques", 20),
    ("Case conceptualization", "Quality of case analysis and formulation", 20),
    ("Ethics and professionalism", "Confidentiality, boundaries, cultural sensitivity", 20),
    ("Documentation", "Timely and complete log book and records", 20),
    ("Reflection and growth", "Use of supervision feedback and self reflection", 20),
]


def seed_default_criteria(db: Session) -> None:
    if db.query(EvaluationCriterionModel).count() > 0:
        return
    for order, (name, description, max_marks) in enumerate(DEFAULT_CRITERIA, start=1):
        db.add(EvaluationCriterionModel(name=name, description=description, max_marks=max_marks, sort_order=order))
    db.commit()


# ------------------------------------------------------------------ rubric
def list_criteria(db: Session, only_active: bool = True):
    query = db.query(EvaluationCriterionModel)
    if only_active:
        query = query.filter(EvaluationCriterionModel.is_active.is_(True))
    return query.order_by(EvaluationCriterionModel.sort_order, EvaluationCriterionModel.id).all()


# ------------------------------------------------------------ who can be graded
def list_supervisees(db: Session, user: UserModel):
    """Admins see every counselor; supervisors see only the counselors assigned to them."""
    query = db.query(UserModel).filter(UserModel.role == SUPERVISEE_ROLE, UserModel.is_active.is_(True))
    if user.role == "admin":
        return query.order_by(UserModel.full_name).all()
    assigned_ids = [
        a.supervisee_id
        for a in db.query(SupervisorAssignmentModel).filter(SupervisorAssignmentModel.supervisor_id == user.id)
    ]
    if not assigned_ids:
        return []
    return query.filter(UserModel.id.in_(assigned_ids)).order_by(UserModel.full_name).all()


# ----------------------------------------------------------- create / read
def create_evaluation(db: Session, evaluator: UserModel, supervisee_id: int, comments, scores: List[dict]):
    if evaluator.role not in SUPERVISOR_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only supervisors can evaluate.")

    if supervisee_id not in {u.id for u in list_supervisees(db, evaluator)}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This counselor is not assigned to you.")

    criteria = {c.id: c for c in list_criteria(db)}
    submitted = {s["criterion_id"]: s for s in scores}
    if len(submitted) != len(scores):
        raise HTTPException(status_code=422, detail="A criterion was scored more than once.")
    if set(submitted) != set(criteria):
        raise HTTPException(status_code=422, detail="Every active criterion must be scored.")

    total = Decimal("0")
    max_total = Decimal("0")
    for cid, criterion in criteria.items():
        marks = Decimal(str(submitted[cid]["marks"]))
        if marks < 0 or marks > criterion.max_marks:
            raise HTTPException(
                status_code=422, detail=f"Marks for '{criterion.name}' must be between 0 and {criterion.max_marks}."
            )
        total += marks
        max_total += criterion.max_marks

    evaluation = EvaluationModel(
        supervisee_id=supervisee_id, evaluator_id=evaluator.id,
        total_marks=total, max_total=max_total, comments=comments,
    )
    db.add(evaluation)
    db.flush()
    for cid, item in submitted.items():
        db.add(EvaluationScoreModel(
            evaluation_id=evaluation.id, criterion_id=cid,
            marks=Decimal(str(item["marks"])), remarks=item.get("remarks"),
        ))
    db.commit()
    db.refresh(evaluation)
    return evaluation


def _present(db: Session, evaluation: EvaluationModel) -> dict:
    data = to_dict(evaluation)
    supervisee = db.get(UserModel, evaluation.supervisee_id)
    evaluator = db.get(UserModel, evaluation.evaluator_id)
    data["supervisee_name"] = supervisee.full_name if supervisee else None
    data["evaluator_name"] = evaluator.full_name if evaluator else None
    data["percent"] = round(data["total_marks"] / data["max_total"] * 100, 1) if data["max_total"] else 0

    rows = (
        db.query(EvaluationScoreModel, EvaluationCriterionModel)
        .join(EvaluationCriterionModel, EvaluationCriterionModel.id == EvaluationScoreModel.criterion_id)
        .filter(EvaluationScoreModel.evaluation_id == evaluation.id)
        .order_by(EvaluationCriterionModel.sort_order, EvaluationCriterionModel.id)
        .all()
    )
    data["scores"] = [
        {
            "criterion_id": c.id, "criterion_name": c.name,
            "max_marks": c.max_marks, "marks": float(s.marks), "remarks": s.remarks,
        }
        for s, c in rows
    ]
    return data


def list_evaluations(db: Session, user: UserModel) -> List[dict]:
    query = db.query(EvaluationModel)
    if user.role == "admin":
        pass
    elif user.role in SUPERVISOR_ROLES:
        query = query.filter(EvaluationModel.evaluator_id == user.id)
    else:
        query = query.filter(EvaluationModel.supervisee_id == user.id)
    return [_present(db, e) for e in query.order_by(EvaluationModel.created_at.desc(), EvaluationModel.id.desc()).all()]


def get_evaluation(db: Session, user: UserModel, evaluation_id: int) -> dict:
    evaluation = db.get(EvaluationModel, evaluation_id)
    allowed = evaluation is not None and (
        user.role == "admin" or user.id in (evaluation.evaluator_id, evaluation.supervisee_id)
    )
    if not allowed:  # same answer for "missing" and "not yours", so ids cannot be probed
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found.")
    return _present(db, evaluation)
