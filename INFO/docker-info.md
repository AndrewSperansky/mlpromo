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
| Просмотр логов приложения | `docker logs -f promo_loki` | Поток логов backend-приложения |
| Просмотр логов Neo4j | `docker logs -f 3dsonet-neo4j` | Контроль запуска и ошибок Neo4j |
| Проверить логи всех контейнеров | `docker compose logs -f` | Поток всех логов окружения |
| Проверить объем данных | `docker system df` | Использование пространства Docker |

---

## 🧰 Отладка / Вход в контейнер

| Цель | Команда | Комментарий |
|------|----------|--------------|
| Войти в backend контейнер | `docker exec -it promo_ml_backend /bin/sh` | Терминал внутри контейнера приложения |
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
`docker-compose logs -f backend`
`docker logs promo_nginx`
`docker logs promo_ml_backend --tail 200`


## ПРОВЕРКИ ПОСЛЕ СТАРТА

curl http://localhost:8000/api/v1/system/health   
— должен вернуть статус OK.

Grafana на http://localhost:3000 (admin/admin).

Loki API http://localhost:3100.

`Redis redis-cli -h localhost -p 6379 ping → PONG.`

`Postgres подключаться на 5432.`

## NGINX

`docker/nginx.conf`    Папка 
`docker exec -it promo_nginx /bin/sh`      Зайти в контейнер  
`#  nginx -t`  
`# nginx -s reload`  
`docker restart promo_nginx`  
`docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"`


### СПИСОК ВСЕХ ПАПОК DOCKER

`docker volume ls`

### Удаление папок из DOCKER

`docker volume rm docker_loki-data`
`docker volume rm promo-ml_loki-data`
`docker volume rm loki-data`


### ПРОВЕРКА КОНТЕЙНЕРА ПО СЛОЯМ !!!!!+++++!!!!

`docker history promo-ml`


### Запускать сборку именно этим образом:

>`docker compose build backend`   
`docker compose up -d`


### ПРОВЕРКА ПАПОК ВНУТРИ КОНТЕЙНЕРА

 `Get-ChildItem -Recurse docker/loki/data`   
 
### Проверка состояния контейнера (стартовал или restarting)
`docker-compose exec loki sh -c "ls -l /var/loki"`   


###  Пути к папкам контейнера

 `docker inspect promo_loki --format='{{json .Mounts}}'`
 
### После замены файлов ОБЯЗАТЕЛЬНО ВЫПОЛНИТЬ:

`docker-compose down -v`  -- Данные будут потеряны



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

## Доступ к папке контейнера
 docker run --rm -it -v promo-ml_logs:/logs alpine ls -l /logs
 
## список volume-ов (ищите те, что начинаются с promo-ml или promo_)
docker volume ls

## какие mount'ы у backend (внимательно посмотрите Destination)
docker inspect promo_ml_backend --format '{{json .Mounts}}' .

## какие mount'ы у nginx
docker inspect promo_nginx --format '{{json .Mounts}}' .


>docker rm — удаление контейнера.  
-f — принудительное удаление (даже запущенного контейнера).  
Пример: docker rm -f my_container.   
docker exec — выполнение команд в запущенном контейнере.  
-it — интерактивный режим.
Пример: docker exec -it my_container /bin/bash — вход в контейнер через терминал.   
docker logs — просмотр логов контейнера.  
-f — слежение за логами в реальном времени.  
--tail <N> — показ последних N строк.  
Пример: docker logs -f my_container.  


>Управление томами  
docker volume create — создание тома.  
docker volume ls — список томов.  
docker volume rm — удаление тома.  
docker volume prune — удаление неиспользуемых томов.  


>docker ps — выводит список запущенных контейнеров.  
-a — показывает все контейнеры, включая остановленные.  
-q — выводит только ID контейнеров. 


## Какой командой пересобрать приложение после изменений?

### Зависит что именно менялось. Вот точная таблица 👇

### 🔁 A. Меняли ТОЛЬКО конфиги (promtail / grafana / alerts)
`docker compose up -d --force-recreate promtail grafana loki`


❌ backend / postgres / redis НЕ трогаем

### 🐍 B. Меняли backend код или logging
`docker compose build promo_ml_backend`  
`docker compose up -d promo_ml_backend`


или короче:

`docker compose up -d --build promo_ml_backend`

### 🐘 C. Меняли postgres.config, promtail-config.yaml
`docker compose up -d --force-recreate postgres`
`docker compose up -d --force-recreate promtail`



⚠️ Образ не пересобирается — только рестарт контейнера

### 📊 D. Добавляем Prometheus + exporters (СКОРО)
`docker compose up -d --build prometheus redis-exporter`

### 🧹 E. Полный жёсткий рестарт (редко!)
`docker compose down`  
`docker compose up -d --build`

Используем только если сломали сеть или volume

### 🔐 !!!! Важное правило !!!!!!

## ⚠️Никогда не делай down -v, если не хочешь потерять данные



## РАБОТА С DOCKER HUB
### 1. Войдите в Docker Hub
docker login

### 2. Соберите образ (если ещё не собран)
docker build -t ваш_логин/название_образа:тег .

### 3. Проверьте список образов
docker images

### 4. Существует ли образ локально
docker images | grep promo-ml   

### 5. Тегируем latest как stage1
`docker tag promo-ml:latest asperansky/promo-ml:stage1`  
🔹 Важно:  
Это не копия, не rebuild — это ещё одна ссылка на тот же image ID.

### 6. Собрать образ (если еще не собран)
`docker build -t asperansky/promo-ml:stage1 . ` 
🔹  -t     задает имя  
🔹 (.)    путь к Dockerfile (текущая директория)


### 7. Отправить образ на Docker Hub
`docker push asperansky/promo-ml:stage1`

### 8. Проверка на Docker Hub
docker inspect asperansky/promo-ml:stage1 | grep Id
