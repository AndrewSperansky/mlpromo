# app/services/audit_service.py


from sqlalchemy import text
from sqlalchemy.orm import Session


def get_audit_page(
    db: Session,
    page: int = 1,
    model_id: int | None = None,
    limit: int = 50,
):

    offset = (page - 1) * limit

    query = """
        SELECT
            id,
            request_id,
            model_id,
            model_version,
            prediction_value,
            created_at
        FROM ml_prediction_audit
    """

    params = {}

    if model_id:
        query += " WHERE model_id = :model_id "
        params["model_id"] = str(model_id)

    query += """
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """

    params["limit"] = limit
    params["offset"] = offset

    rows = db.execute(text(query), params).mappings().all()

    total = db.execute(
        text("SELECT COUNT(*) FROM ml_prediction_audit")
    ).scalar()

    return {
        "items": rows,
        "page": page,
        "total": total,
    }