from sqlalchemy.orm import Session
from typing import Type, Any
from sqlalchemy import select


def get_or_create(
    db: Session,
    model: Type[Any],
    filters: dict,
    defaults: dict | None = None,
):
    stmt = select(model).filter_by(**filters)
    instance = db.execute(stmt).scalar_one_or_none()

    if instance:
        if defaults:
            for k, v in defaults.items():
                setattr(instance, k, v)
        return instance, False

    params = {**filters, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    return instance, True
