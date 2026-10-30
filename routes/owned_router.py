from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.userM import UserModel
from services.authService import get_current_user
from services.ownedRecordService import (
    create_owned, delete_owned, get_owned, list_owned, update_owned,
)
from services.serializeUtil import to_dict


def _payload(data) -> dict:
    return data.model_dump() if hasattr(data, "model_dump") else data.dict()


def build_owned_router(prefix: str, tag: str, model, schema, order_column: str) -> APIRouter:
    """Router with list / get / create / update / delete for a per-user table.

    The user comes from the Bearer token, never from the request, so a user can only
    touch their own rows.
    """
    router = APIRouter(prefix=prefix, tags=[tag])
    order_by = getattr(model, order_column)

    @router.get("/")
    def list_records(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
        rows = list_owned(db, model, user.id, order_by)
        return {"status": "success", "data": [to_dict(r) for r in rows]}

    @router.get("/{record_id}")
    def get_record(record_id: int, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
        return {"status": "success", "data": to_dict(get_owned(db, model, user.id, record_id))}

    @router.post("/", status_code=status.HTTP_201_CREATED)
    def create_record(data: schema, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
        return {"status": "success", "data": to_dict(create_owned(db, model, user.id, _payload(data)))}

    @router.put("/{record_id}")
    def update_record(
        record_id: int, data: schema,
        user: UserModel = Depends(get_current_user), db: Session = Depends(get_db),
    ):
        return {"status": "success", "data": to_dict(update_owned(db, model, user.id, record_id, _payload(data)))}

    @router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_record(record_id: int, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
        delete_owned(db, model, user.id, record_id)

    return router
