## Поиск по всему приложению app/
grep -R "settings\.ENV" -n app  
grep -R "settings\.VERSION" -n app

docker desktop stop --force


🧪 SMOKE TEST (фиксируем)
curl http://localhost:8000/api/v1/system/health
curl http://localhost:8000/api/v1/system/health/db
curl http://localhost:8000/api/v1/system/health/server

docker inspect --format='{{.State.Health.Status}}' promo_ml_backend
docker ps --format "table {{.Names}}\t{{.ID}}\t{{.Status}}\t{{.Ports}}"
docker ps


docker logs --tail=50 promo_ml_backend

Ожидаем: "Application startup complete."




docker volume inspect promo_postgres_data
