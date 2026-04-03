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
        """
        Извлекает фичи из запроса
        """
        logger.info(f"🔍 DEBUG: request keys = {list(request.keys())}")
        logger.info(f"🔍 DEBUG: request content = {request}")

        features = {}
        missing_required = []  # ← собираем отсутствующие обязательные поля

        for f in self.config.get('inference_features', []):
            name = f['name']
            default = f.get('default', '')
            required = f.get('required', False)
            value_type = f.get('type', 'string')

            value = request.get(name, default)

            # Преобразуем тип
            if value_type in ['integer', 'int']:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    value = int(default) if default else 0
            elif value_type in ['number', 'float']:
                try:
                    value = float(value)
                except (TypeError, ValueError):
                    value = float(default) if default else 0.0
            elif value_type in ['boolean', 'bool']:
                if isinstance(value, str):
                    value = value.lower() in ['true', '1', 'yes']
                else:
                    value = bool(value)
            elif value_type in ['array', 'list']:
                if isinstance(value, str):
                    import json
                    value = json.loads(value) if value else []
                else:
                    value = value if isinstance(value, list) else []
            else:  # string
                value = str(value) if value is not None else ''

            features[name] = value

            if required and (value is None or value == '' or value == 0):
                missing_required.append(name)
                logger.warning(f"Required feature '{name}' is missing, using default: {default}")

            # 🔥 Если есть отсутствующие обязательные поля — бросаем ошибку
        if missing_required:
            raise ValueError(f"Missing required features: {', '.join(missing_required)}")

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