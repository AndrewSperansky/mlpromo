# app/ml/dataset/ml_dataset.py

from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session
import pandas as pd


def fetch_features(
    db: Session,
    promo_code: str,
    sku: str,
    target_date: date,
) -> tuple[pd.DataFrame, bool]:
    """
    Returns:
        (features_df, fallback_used)
    """

    sql = text("""
        SELECT
            price,
            discount,
            avg_sales_7d,
            avg_discount_7d,
            promo_days_left
        FROM promo_ml_dataset_v1
        WHERE promo_code = :promo_code
          AND sku = :sku
          AND date = :target_date
    """)

    df = pd.read_sql(
        sql,
        db.bind,
        params={
            "promo_code": promo_code,
            "sku": sku,
            "target_date": target_date,
        },
    )

    if not df.empty:
        return df, False

    # 🔁 FALLBACK — last known snapshot
    fallback_sql = text("""
        SELECT
            price,
            discount,
            avg_sales_7d,
            avg_discount_7d,
            promo_days_left
        FROM promo_ml_dataset_v1
        WHERE promo_code = :promo_code
          AND sku = :sku
          AND date < :target_date
        ORDER BY date DESC
        LIMIT 1
    """)

    df = pd.read_sql(
        fallback_sql,
        db.bind,
        params={
            "promo_code": promo_code,
            "sku": sku,
            "target_date": target_date,
        },
    )

    if df.empty:
        raise ValueError("No features found for prediction")

    return df, True
