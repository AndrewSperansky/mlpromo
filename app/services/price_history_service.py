# app/services/price_history_service.py

from sqlalchemy.orm import Session
from datetime import date, timedelta
from sqlalchemy import text


class PriceHistoryService:

    def __init__(self, db: Session):
        self.db = db

    def get_retail_price_history(self, sku: str, days: int = 30) -> list[dict]:
        """Возвращает историю продажных цен за последние N дней"""
        result = self.db.execute(
            text("""
                SELECT date, price
                FROM retail_price_history
                WHERE sku = :sku AND date >= CURRENT_DATE - :days
                ORDER BY date
            """),
            {"sku": sku, "days": days}
        )
        return [{"date": row[0], "price": float(row[1])} for row in result.fetchall()]

    def get_purchase_price_history(self, sku: str, supplier: str, days: int = 30) -> list[dict]:
        """Возвращает историю закупочных цен за последние N дней"""
        result = self.db.execute(
            text("""
                SELECT date, price
                FROM purchase_price_history
                WHERE sku = :sku AND supplier = :supplier AND date >= CURRENT_DATE - :days
                ORDER BY date
            """),
            {"sku": sku, "supplier": supplier, "days": days}
        )
        return [{"date": row[0], "price": float(row[1])} for row in result.fetchall()]
