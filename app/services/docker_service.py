# app/services/docker_service.py

import docker
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from docker.errors import NotFound

logger = logging.getLogger("promo_ml")


class DockerService:
    """Сервис для получения статуса Docker контейнеров"""

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker client initialization failed: {e}")
            self.client = None

    def get_containers_status(self, container_names: List[str] = None) -> Dict[str, Any]:
        """
        Возвращает статус указанных контейнеров.
        Если container_names не указаны — возвращает все контейнеры с меткой promo_
        """
        if not self.client:
            return {"error": "Docker client not available", "containers": {}}

        try:
            # Если имена не указаны — берём все контейнеры с promo_ в имени
            if container_names is None:
                all_containers = self.client.containers.list(all=True)
                containers = {}
                for c in all_containers:
                    if c.name.startswith("promo_"):
                        containers[c.name] = self._get_container_status(c)
            else:
                containers = {}
                for name in container_names:
                    try:
                        c = self.client.containers.get(name)
                        containers[name] = self._get_container_status(c)
                    except docker.errors.NotFound:
                        containers[name] = {
                            "status": "not_found",
                            "state": "missing",
                            "health": "unknown",
                            "error": f"Container {name} not found"
                        }

            return {
                "success": True,
                "containers": containers,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get containers status: {e}")
            return {
                "success": False,
                "error": str(e),
                "containers": {}
            }

    def _get_container_status(self, container) -> Dict[str, Any]:
        """Формирует статус одного контейнера"""
        status = container.status
        state = container.attrs.get("State", {})
        health = state.get("Health", {}).get("Status", "unknown")

        # Если health check не настроен, используем статус контейнера
        if health == "unknown" and status == "running":
            health = "healthy"

        return {
            "status": status,
            "state": state.get("Status", status),
            "health": health,
            "running": status == "running",
            "healthy": health == "healthy" or (status == "running" and health == "unknown"),
            "started_at": state.get("StartedAt", ""),
            "image": container.image.tags[0] if container.image.tags else "unknown"
        }