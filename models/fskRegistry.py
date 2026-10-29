"""
models/fskRegistry.py - FSK UPSI directory of people allowed to register.

Registration is only possible for an identifier (matric / staff ID) that exists
in this table. Name, email and role come from here, NOT from the client, so a
user cannot self-assign the "supervisor" role.
"""
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, text

from database import Base


class FskRegistryModel(Base):
    __tablename__ = "fsk_registry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    identifier = Column(String(50), unique=True, index=True, nullable=False)  # matric / staff ID
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False)  # supervisor | field supervisor | counselor
    # Set once the person has registered. NULL = not registered yet.
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        unique=True,
        nullable=True,
    )
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )


# -------------------------------------------------------------------
# Request / response schemas
# -------------------------------------------------------------------
class LookupResponse(BaseModel):
    fullName: str
    email: str
    role: str


class RegisterRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=128)
