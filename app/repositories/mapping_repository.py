# app/repositories/mapping_repository.py
# Пока не используем!!!  VOID

import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import SessionLocal

logger = logging.getLogger("promo_ml")


class MappingRepository:
    """
    Репозиторий для получения маппингов promo_code/sku в числовые идентификаторы.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self._promo_cache: Dict[str, int] = {}
        self._sku_cache: Dict[str, int] = {}
        self._cache_initialized = False

    def _init_cache(self):
        """Инициализирует кэш маппингов"""
        if self._cache_initialized:
            return

        try:
            # Загружаем все promo_code в кэш
            promo_result = self.db.execute(
                text("""
                SELECT DISTINCT promo_code, CAST(ABS(('x' || substr(md5(promo_code), 1, 8))::bit(32)::int) % 1000 AS integer) as code_id
                FROM promo
                WHERE promo_code IS NOT NULL
                """)
            ).all()

            for row in promo_result:
                self._promo_cache[row.promo_code] = row.code_id

            # Загружаем все sku в кэш
            sku_result = self.db.execute(
                text("""
                SELECT DISTINCT sku, CAST(ABS(('x' || substr(md5(sku), 1, 8))::bit(32)::int) % 10000 AS integer) as sku_id
                FROM products
                WHERE sku IS NOT NULL
                """)
            ).all()

            for row in sku_result:
                self._sku_cache[row.sku] = row.sku_id

            self._cache_initialized = True
            logger.info(
                "Mapping cache initialized",
                extra={
                    "promo_codes": len(self._promo_cache),
                    "skus": len(self._sku_cache),
                },
            )

        except Exception as e:
            logger.error("Failed to initialize mapping cache", extra={"error": str(e)})
            raise

    def get_promo_code_id(self, promo_code: str) -> int:
        """
        Возвращает числовой ID для promo_code.
        Если не найден - генерирует новый.
        """
        self._init_cache()

        if promo_code in self._promo_cache:
            return self._promo_cache[promo_code]

        # Генерируем новый ID для неизвестного promo_code
        import hashlib
        new_id = int(hashlib.md5(promo_code.encode()).hexdigest()[:8], 16) % 1000

        # Сохраняем в БД для будущих запросов
        try:
            self.db.execute(
                text("""
                INSERT INTO promo_code_mapping (promo_code, code_id)
                VALUES (:promo_code, :code_id)
                ON CONFLICT (promo_code) DO NOTHING
                """),
                {"promo_code": promo_code, "code_id": new_id},
            )
            self.db.commit()
            self._promo_cache[promo_code] = new_id
        except Exception as e:
            logger.warning(
                "Failed to persist new promo_code mapping",
                extra={"promo_code": promo_code, "error": str(e)},
            )
            self.db.rollback()

        return new_id

    def get_sku_id(self, sku: str) -> int:
        """
        Возвращает числовой ID для sku.
        Если не найден - генерирует новый.
        """
        self._init_cache()

        if sku in self._sku_cache:
            return self._sku_cache[sku]

        # Генерируем новый ID для неизвестного sku
        import hashlib
        new_id = int(hashlib.md5(sku.encode()).hexdigest()[:8], 16) % 10000

        # Сохраняем в БД для будущих запросов
        try:
            self.db.execute(
                text("""
                INSERT INTO sku_mapping (sku, sku_id)
                VALUES (:sku, :sku_id)
                ON CONFLICT (sku) DO NOTHING
                """),
                {"sku": sku, "sku_id": new_id},
            )
            self.db.commit()
            self._sku_cache[sku] = new_id
        except Exception as e:
            logger.warning(
                "Failed to persist new sku mapping",
                extra={"sku": sku, "error": str(e)},
            )
            self.db.rollback()

        return new_id

    def close(self):
        """Закрывает сессию БД"""
        if self.db:
            self.db.close()