# app/api/v1/ml/dataset.py

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import SessionLocal


def load_dataset(limit: int = 10_000) -> pd.DataFrame:

    db: Session = SessionLocal()

    sql = text("""
        SELECT
            date,
            promo_code,
            sku,
            price,
            discount,
            target_sales_qty,
            avg_sales_7d,
            avg_discount_7d,
            promo_days_left
        FROM promo_ml_dataset_v1
        ORDER BY date
        LIMIT :limit
    """)

    df = pd.read_sql(
        sql,
        db.bind,
        params={"limit": limit},
    )

    db.close()

    return df