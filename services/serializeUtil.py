from datetime import date, datetime
from decimal import Decimal


def to_dict(obj) -> dict:
    """Convert a SQLAlchemy row to a JSON-safe dict (dates -> ISO strings, Decimal -> float)."""
    out = {}
    for col in obj.__table__.columns:
        value = getattr(obj, col.name)
        if isinstance(value, (date, datetime)):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = float(value)
        out[col.name] = value
    return out
