# 🧭 Docker Cheatsheet — 3D SoNet

# Таблица для управления окружением проекта
### Включает все команды для запуска, проверки, мониторинга и отладки контейнеров.

---
## Сборка (Монтировка)

| Цель | Команда                                                       | Комментарий                                                                                |
|------|---------------------------------------------------------------|--------------------------------------------------------------------------------------------|
|      | docker-compose up -d                                          | Не пересобирает образ, запускает то что есть                                               |
|      | docker-compose up -d --build backend                          | Если не меняешь requirements.txt и Dockerfile Сборка идёт быстро — внутри кеш остаётся     |
|      | docker-compose up -d --no-deps backend                        | Если меняются только файлы конфигурайии (nginx.conf, promtail-config.yml, loki-config.yml) |
|      | docker-compose build backend                  |  самый длинный и болезненный случай — пересобираются оба слоя (builder + runtime)  |
|      | `docker-compose up -d --build`                                |                                                                                            |
|   | `docker build -t promo-ml-backend .`                          | from repo root                                                                             |
|    | `docker-compose build --parallel`                             |                                                                                            |
|   | `docker build -t promo-ml-mlworker -f docker/Dockerfile.ml .` |                                                                                            |

Аналогично docker-compose up -d --no-deps backend     
Если меняются только файлы конфигурайии (nginx.conf, promtail-config.yml, loki-config.yml)
>`docker restart promo_loki`\
`docker restart promo_promtail`\
`docker restart promo_nginx`



## 🚀 Запуск

| Цель | Команда | Комментарий                        |
|------|----------|------------------------------------|
|      |docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"| Вывод как Docker Desktop      |
|      |docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Проверь все контейнеры          |
|      |         |                                    |
| Запустить окружение | `docker compose up -d` | Запускает все контейнеры (в фоне)  |
| Пересобрать и запустить | `docker compose up --build -d` | Собирает заново образы и запускает |
| Остановить контейнеры | `docker compose down` | Останавливает и удаляет контейнеры |
| Перезапустить всё | `docker compose down && docker compose up -d` | Полный рестарт окружения           |
| Просмотреть статус | `docker ps --format "table {{.Names}}\t{{.Status}}"   | Проверяет, какие контейнеры запущены |

>`docker ps --format "table {{.Names}}\t{{.Status}}" | grep 3dsonet` 
> 
> `docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" |
    Select-String "promo-ml" `
---

## 🧠 Проверка

| Цель | Команда | Комментарий |
|------|----------|--------------|
| Проверить всё окружение | `./check.sh` | Скрипт автоматической проверки всех сервисов |
| Проверить Neo4j | `docker exec -it 3dsonet-neo4j cypher-shell -u neo4j -p neo4jpassword "RETURN 1;"` | Тест подключения к БД Neo4j |
| Проверить PostgreSQL | `docker exec -it 3dsonet-db psql -U postgres -c "SELECT 1;"` | Проверка доступности базы |
| Проверить Redis | `docker exec -it 3dsonet-redis redis-cli ping` | Ответ должен быть `PONG` |
| Проверить backend | `docker logs 3dsonet-app | grep "listening"` | Убедиться, что сервер запущен |

---

## 🔍 Мониторинг / Логи

| Цель | Команда | Комментарий |
|------|----------|--------------|
| Просмотр логов приложения | `docker logs -f 3dsonet-app` | Поток логов backend-приложения |
| Просмотр логов Neo4j | `docker logs -f 3dsonet-neo4j` | Контроль запуска и ошибок Neo4j |
| Проверить логи всех контейнеров | `docker compose logs -f` | Поток всех логов окружения |
| Проверить объем данных | `docker system df` | Использование пространства Docker |

---

## 🧰 Отладка / Вход в контейнер

| Цель | Команда | Комментарий |
|------|----------|--------------|
| Войти в backend контейнер | `docker exec -it 3dsonet-app /bin/sh` | Терминал внутри контейнера приложения |
| Войти в PostgreSQL | `docker exec -it 3dsonet-db psql -U postgres` | Консоль PostgreSQL |
| Войти в Redis | `docker exec -it 3dsonet-redis redis-cli` | Консоль Redis |
| Войти в Neo4j | `docker exec -it 3dsonet-neo4j cypher-shell -u neo4j -p neo4jpassword` | Консоль Neo4j |
| Очистить кеш npm | `docker exec -it 3dsonet-app npm cache clean --force` | Безопасная очистка кеша npm |
| Пересобрать только backend | `docker compose build app` | Быстрая пересборка без остальных контейнеров |

---

## УДАЛЕНИЕ НЕНУЖНОГО ОБРАЗА

`docker compose down`
`docker rmi promo-ml-backend:latest`



## ПЕРЕСБОРКА КОНТЕЙНЕРА app


docker compose build app    ` Быстрая пересборка без остальных контейнеров |  Пересобрать только backend `   

docker-compose down

docker-compose down -v      `Останавливает контейнеры и удаляет все (контейнеры + сеть + volumes с данными)`\
                            `дополнительно удаляет named volumes, объявленные в docker-compose.yml. То есть:`\
>volumes:\
  >postgres_data:\
  >grafana_data:\
  >loki-data:


### Диагностика внутри promtail-контейнера:

`docker exec -it promo_promtail sh`\
`ls /logs`

Проверить логи

`docker logs promo_promtail`\
`docker logs promo_loki`


 ### Диагностировать и Удалить только Postgres volume:

`docker logs promo_postgres`\
`docker stop promo_postgres`\
`docker rm promo_postgres`\
`docker volume ls`\
`docker volume rm promo-ml_postgres_data`

`docker-compose build --no-cache app`

`docker-compose up -d`

`docker-compose logs -f app`\  
покажет, что NestJS и GraphQL запускаются без ошибок.




### 1️⃣ Посмотрим список всех контейнеров

`docker ps -a`  
`docker ps`

### 2️⃣ Посмотрим список сервисов из твоего docker-compose

####  Если compose лежит в папке docker/, выполняем:

`docker-compose -f docker/docker-compose.yml config`

#### (или если ты используешь docker compose новую версию)

`docker compose -f docker/docker-compose.yml config`

##  ЛОГИРОВАНИЕ

>docker logs loki  
docker logs promtail  
docker logs grafana  
docker-compose logs -f backend
docker logs promo_nginx


## ПРОВЕРКИ ПОСЛЕ СТАРТА

curl http://localhost:8000/api/v1/system/health   
— должен вернуть статус OK.

Grafana на http://localhost:3000 (admin/admin).

Loki API http://localhost:3100.

`Redis redis-cli -h localhost -p 6379 ping → PONG.`

`Postgres подключаться на 5432.`

## NGINX

`docker/nginx.conf`


## СПИСОК ВСЕХ ПАПОК DOCKER

`docker volume ls`

## Удаление папок из DOCKER

`docker volume rm docker_loki-data`
`docker volume rm promo-ml_loki-data`
`docker volume rm loki-data`

## Создать директории вручную (важно для Windows!)

`mkdir docker/loki/data`
`mkdir docker/loki/data/index`
`mkdir docker/loki/data/chunks`
`mkdir docker/loki/data/compactor`

## ПРОВЕРКА КОНТЕЙНЕРА ПО СЛОЯМ !!!!!+++++!!!!

`docker history promo-ml`


# Запускать сборку именно этим образом:

>`docker compose build backend`   
`docker compose up -d`


# ПРОВЕРКА ПАПОК ВНУТРИ КОНТЕЙНЕРА

 `Get-ChildItem -Recurse docker/loki/data`   
 
### Проверка состояния контейнера (стартовал или restarting)
`docker-compose exec loki sh -c "ls -l /var/loki"`   


##  Пути к папкам контейнера

 `docker inspect promo_loki --format='{{json .Mounts}}'`
 
## После замены файлов ОБЯЗАТЕЛЬНО ВЫПОЛНИТЬ:

`docker-compose down -v`  
`


## Как войти  в контейнер если он перезапускается

`docker update --restart=no promo_ml_backend`  
`docker start promo_ml_backend`   
`docker exec -it promo_ml_backend /bin/sh`  
затем быстро пока не упал   
`$`  новое приглашение (не вводится)   
`$   ls -la /app/logs`  
`$   chmod 7777 /app/logs`  даем полные права  
`$   chown 1000:1000 /app/log` меняем пользователя  
`$   chmod g+w /app/logs`  даем права на запись группе   