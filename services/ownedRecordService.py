"""Generic CRUD for tables where every row belongs to one user (user_id column).

Used by self reflection, psychoeducation and professional development.
A user can only ever see or change their own rows.
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def list_owned(db: Session, model, user_id: int, order_by):
    return db.query(model).filter(model.user_id == user_id).order_by(order_by.desc(), model.id.desc()).all()


def get_owned(db: Session, model, user_id: int, record_id: int):
    record = db.query(model).filter(model.id == record_id, model.user_id == user_id).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    return record


def create_owned(db: Session, model, user_id: int, data: dict):
    record = model(user_id=user_id, **data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_owned(db: Session, model, user_id: int, record_id: int, data: dict):
    record = get_owned(db, model, user_id, record_id)
    for key, value in data.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record


def delete_owned(db: Session, model, user_id: int, record_id: int) -> None:
    record = get_owned(db, model, user_id, record_id)
    db.delete(record)
    db.commit()
