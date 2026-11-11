# app/ml/feature_pipeline.py

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Callable

logger = logging.getLogger("promo_ml")


class FeaturePipeline:
    """
    Конвейер сборки фич для модели.
    Только трансформация данных, без доступа к БД.
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "feature_config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        self._formula_cache: Dict[str, Callable] = {}
        logger.info(f"FeaturePipeline initialized with {len(self.config.get('inference_features', []))} features")

    def build_features(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Собирает полный набор фич для модели
        """
        logger.info(f"🔍 DEBUG: build_features request keys = {list(request.keys())}")

        features = {}

        # 1. Базовые фичи из запроса
        features.update(self._extract_inference_features(request))

        # 2. Вычисляемые фичи
        features.update(self._compute_features(features))

        logger.info(f"🔍 DEBUG: features after extraction = {list(features.keys())}")

        return features

    def _extract_inference_features(self, request: Dict) -> Dict:
        features = {}
        for f in self.config.get('inference_features', []):
            name = f['name']
            default = f.get('default', '')
            value = request.get(name, default)

            # 🔥 НЕ ПЫТАЕМСЯ КОНВЕРТИРОВАТЬ store_id В ЧИСЛО!
            if name in ['store_id', 'sku', 'promo_id', 'category', 'region',
                        'store_location_type', 'format_assortment',
                        'promo_mechanics', 'adv_carrier', 'adv_material',
                        'marketing_type']:
                value = str(value) if value is not None else ''
            elif isinstance(value, (int, float)):
                value = float(value)
            else:
                value = str(value) if value is not None else ''

            features[name] = value
        return features



    def _compute_features(self, features: Dict) -> Dict:
        """Вычисляет производные фичи"""
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