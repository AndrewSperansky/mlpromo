# app/ml/feature_pipeline.py

import yaml
import logging
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models.industrial_dataset import IndustrialDatasetRaw
import redis

logger = logging.getLogger("promo_ml")


class FeaturePipeline:
    """
    Гибкий конвейер сборки фич на основе YAML-конфигурации.
    Источник данных: industrial_dataset_raw.
    """

    def __init__(self, db: Session, redis_client: redis.Redis, config_path: str = None):
        self.db = db
        self.redis = redis_client

        # Загружаем конфигурацию
        if config_path is None:
            config_path = Path(__file__).parent / "feature_config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        # Кэш для вычисленных формул
        self._formula_cache: Dict[str, Callable] = {}

        logger.info(
            f"FeaturePipeline initialized with {len(self.config.get('inference_features', []))} inference features"
        )

    def build_features(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Собирает полный набор фич для модели.
        """
        features = {}

        # 1. Базовые фичи из запроса
        features.update(self._extract_inference_features(request))

        # 2. Вычисляемые фичи (например, percent_price_drop)
        features.update(self._compute_features(features))

        # 3. Категориальные поля из industrial_dataset_raw (sku_level_2, region и т.д.)
        features.update(self._lookup_features(features))

        # 4. 52 недели продаж из industrial_dataset_raw
        weekly_sales = self._get_weekly_sales(
            sku=features.get("sku", ""),
            store_id=features.get("store_id", "")
        )
        features.update(weekly_sales)

        # 5. Агрегатные фичи (исторические продажи за 30/60/90/180 дней) — пока заглушка
        features.update(self._aggregate_features(features))

        # 6. Сезонные коэффициенты — пока заглушка
        features.update(self._seasonal_features(features))

        # 7. Месячные продажи — пока заглушка
        features.update(self._monthly_features(features))

        # 8. Праздничные флаги — пока заглушка
        features.update(self._holiday_features(features))

        return features

    def _extract_inference_features(self, request: Dict) -> Dict:
        """Извлекает фичи из запроса согласно конфигурации"""
        features = {}

        for f in self.config.get('inference_features', []):
            name = f['name']
            default = f.get('default', 0)
            required = f.get('required', False)

            value = request.get(name, default)

            # Преобразуем тип
            if f['type'] == 'float':
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    value = default
            elif f['type'] == 'bool':
                value = 1 if value else 0
            elif f['type'] == 'string':
                value = str(value) if value else ''

            features[name] = value

            if required and (value is None or value == ''):
                logger.warning(f"Required feature '{name}' is missing, using default: {default}")

        return features

    def _compute_features(self, features: Dict) -> Dict:
        """Вычисляет производные фичи по формулам"""
        result = {}

        for f in self.config.get('computed_features', []):
            name = f['name']
            formula = f['formula']

            if name not in self._formula_cache:
                try:
                    func = eval(f"lambda f: {formula}")
                    self._formula_cache[name] = func
                except Exception as e:
                    logger.error(f"Failed to compile formula for {name}: {e}")
                    result[name] = f.get('default', 0)
                    continue

            try:
                result[name] = self._formula_cache[name](features)
            except Exception as e:
                logger.warning(f"Failed to compute {name}: {e}")
                result[name] = f.get('default', 0)

        return result

    def _lookup_features(self, features: Dict) -> Dict:
        """Подтягивает категориальные фичи из industrial_dataset_raw"""
        result = {}

        for f in self.config.get('lookup_features', []):
            name = f['name']
            source = f['source']
            key_field = f['key']
            lookup_field = f['field']
            cache_ttl = f.get('cache_ttl', 3600)
            default = f.get('default', 0)

            key_value = features.get(key_field)
            if not key_value:
                result[name] = default
                continue

            # Кэш
            cache_key = self._generate_cache_key(source, key_value, lookup_field)
            cached = self.redis.get(cache_key)

            if cached:
                value = cached.decode()
                if f['type'] == 'float':
                    value = float(value)
                elif f['type'] == 'bool':
                    value = 1 if value else 0
                result[name] = value
                continue

            # Запрос в БД
            value = self._query_lookup(source, key_value, lookup_field, f['type'])

            if value is None:
                value = default
            else:
                self.redis.setex(cache_key, cache_ttl, str(value))

            result[name] = value

        return result

    def _generate_cache_key(self, source: str, key: str, field: str) -> str:
        raw_key = f"lookup:{source}:{key}:{field}"
        return f"lookup:{hashlib.md5(raw_key.encode()).hexdigest()[:16]}"

    def _query_lookup(self, source: str, key: str, field: str, value_type: str) -> Optional[Any]:
        """
        Запрос в industrial_dataset_raw.
        """
        try:
            if source == 'industrial_dataset':
                from models.industrial_dataset import IndustrialDatasetRaw

                # Определяем, по какому полю искать
                # Если поле относится к магазину — фильтруем по store_id
                if field in ['store_location_type', 'region', 'format_assortment']:
                    record = self.db.query(IndustrialDatasetRaw).filter_by(store_id=key).first()
                else:
                    # Иначе — по sku
                    record = self.db.query(IndustrialDatasetRaw).filter_by(sku=key).first()

                if record:
                    value = getattr(record, field, None)
                    if value is not None:
                        return value
                else:
                    logger.debug(f"No record found for {source} with key={key}")

            else:
                logger.warning(f"Unknown lookup source: {source}")

            return None

        except ImportError as e:
            logger.error(f"Failed to import model for source {source}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error querying {source} for {key}: {e}")
            return None

    def _get_weekly_sales(self, sku: str, store_id: str) -> Dict[str, float]:
        """
        Загружает 52 недели продаж из industrial_dataset_raw.
        Возвращает словарь {f"reg_sales_qty_week_{i}": value}.
        """
        result = {}

        try:


            record = self.db.query(IndustrialDatasetRaw).filter_by(
                sku=sku,
                store_id=store_id
            ).first()

            if record:
                for i in range(1, 53):
                    field_name = f"reg_sales_qty_week_{i}"
                    value = getattr(record, field_name, None)
                    result[field_name] = float(value) if value is not None else 0.0
            else:
                logger.warning(f"No weekly sales data for SKU={sku}, store={store_id}")
                for i in range(1, 53):
                    result[f"reg_sales_qty_week_{i}"] = 0.0

        except ImportError as e:
            logger.error(f"Failed to import IndustrialDatasetRaw: {e}")
            for i in range(1, 53):
                result[f"reg_sales_qty_week_{i}"] = 0.0
        except Exception as e:
            logger.error(f"Error loading weekly sales for {sku}/{store_id}: {e}")
            for i in range(1, 53):
                result[f"reg_sales_qty_week_{i}"] = 0.0

        return result

    # Ниже — методы-заглушки для возможных будущих расширений.
    # Они могут быть реализованы позже, если появятся соответствующие данные.

    def _aggregate_features(self, features: Dict) -> Dict:
        """Агрегатные фичи (исторические продажи за 30/60/90/180 дней) — заглушка"""
        result = {}
        for f in self.config.get('aggregate_features', []):
            name = f['name']
            result[name] = f.get('default', 0)
        return result

    def _seasonal_features(self, features: Dict) -> Dict:
        """Сезонные коэффициенты — заглушка"""
        result = {}
        for f in self.config.get('seasonal_features', []):
            name = f['name']
            result[name] = f.get('default', 1.0)
        return result

    def _monthly_features(self, features: Dict) -> Dict:
        """Месячные продажи — заглушка"""
        result = {}
        for m in self.config.get('monthly_features', []):
            regular_name = m['regular']
            weekend_name = m['weekend']
            result[regular_name] = 0
            result[weekend_name] = 0
        return result

    def _holiday_features(self, features: Dict) -> Dict:
        """Праздничные флаги — заглушка"""
        result = {}
        for f in self.config.get('holiday_features', []):
            name = f['name']
            result[name] = f.get('default', 0)
        return result