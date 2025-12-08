# Запускаем Loki + Promtail в docker-compose.yml

cd docker
docker-compose -f docker-compose.yml -f docker-compose.logging.yml up -d


## Команды — сборка и запуск (в твоём рабочем окружении)
## из папки docker/
docker-compose build --parallel
docker-compose up -d

## посмотреть логи
docker-compose logs -f backend


## Если образы большие — можно отдельно собирать:

docker build -t promo-ml-backend .            # from repo root
docker build -t promo-ml-mlworker -f docker/Dockerfile.ml .

## Проверки после старта

curl http://localhost:8000/api/v1/system/health — должен вернуть статус OK.

Grafana на http://localhost:3000 (admin/admin).

Loki API http://localhost:3100.

Redis redis-cli -h localhost -p 6379 ping → PONG.

Postgres подключаться на 5432.