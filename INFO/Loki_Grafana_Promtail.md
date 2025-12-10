# 🎯 Большой итог:

# 📌 DEV

читаем логи прямо из logs/…
используем tail -f, VSCode, фильтры

# 📌 PROD

пишем в Docker volume /app/logs
обязательно оставляем Console transport
подключаем Loki или ELK (готовлю конфиг по запросу)

# 📌 Правила

потоковые логи → в файл
важные ошибки → PostgreSQL
GraphQL → JSON файл
HTTP → обычные .log


## ✔ Loki — централизованное хранилище логов
## ✔ Promtail — агент, который читает файлы логов из ./logs внутри контейнера
## ✔ Grafana — мощный UI для просмотра, фильтрации и анализа логов
## ✔ Поддержка JSON и обычных текстовых логов





## КАК ЗАЙТИ в Grafana
================================

### После docker compose up -d:

## Grafana:

👉 http://localhost:3001

`login: admin`  
`password: admin`

### Grafana попросит сменить пароль — можно оставить прежний.


## Подключение Loki внутри Grafana


### В Grafana → Connections → Loki

## URL:
http://loki:3100

### Сохранить → Explore → Logs

### Дальше ты увидишь:

`job = promo-ml`  
`job = graphql`

    и сможешь фильтровать всё что угодно
      🎉 Стек готов!  

### Получаем полноценную production-архитектуру логирования:

### ✔ Winston → local files
### ✔ Docker volume → Promtail
### ✔ Promtail → Loki
### ✔ Loki → Grafana

=============================================================


## Логи каждого контейнера

>`docker logs loki`  
`docker logs promo_loki --tail 50`  
curl http://localhost:3100/ready  

>`docker logs promtail`   
`docker logs promo_promtail --tail 50`    

>`docker logs grafana`  


## Полный перезапуск:

>`docker compose stop loki`  
`docker compose rm -f loki`  
`docker compose up -d loki`  


## поднять права на volume Loki вручную

### Выполнить:

docker exec -it loki sh
chmod -R 777 /loki
exit

### Но это сработает только если Loki хоть немного стартует.


# Как проверить, что Loki работает правильно

### Открой эти URL:

## 1️⃣ Build info
http://localhost:3100/loki/api/v1/status/buildinfo

## 2️⃣ Ready
http://localhost:3100/ready

## Проверка конфигурации
http://localhost:3100/config

## 3️⃣ Метрики
http://localhost:3100/metrics


### Если один из этих URL показывает JSON или текст — Loki работает.

===================================================================

## 1️⃣ Запрос в Explore (UI GRAFANA):
{job=~".+"}
{job="3dsonet"}
{job="graphql"}


## 2️⃣ Содержимое каталога логов в контейнере Promtail:
docker exec -it promtail ls -lR /app/logs

## Проверка Promtail из контейнера
### Видит ли Promtail файлы логов

docker exec -it promtail ls -lR /app/logs

docker exec -it promtail ls -l /app/logs


## У приложения есть ли вообще логи в /app/logs?

### Зайти в контейнер loki:

docker exec -it loki sh
ls -R /app/logs



## Проверяем, идут ли стримы в Loki

http://localhost:3100/loki/api/v1/labels


## Проверяем Promtail

docker logs promtail --tail=200


### Проверить PROMTAIL

docker logs promtail --tail=100

#### Если Promtail не может подключиться к Loki — логи не появятся в Grafana.

### Посмотреть  контейнеры в Docker Desktop

`docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"`

### Посмотреть контейнеры название

`docker volume ls`

### Удалить данные контейнера
`docker volume rm docker_postgres_data`

### Проверить все контейнеры:

`docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" `


### Проверь логи promtail:

`docker logs promo_promtail`


### Проверить что логи попадают:

http://localhost:3100/ready
http://localhost:3100/metrics


### Проверить Grafana:

http://localhost:3000

`login: admin / admin`


### Проверка папок в контейнере
`docker-compose exec loki sh -c "ls -l /var/loki"`  

> if  "is restarting"

`docker run --rm -it -v ./docker/loki/data:/var/loki alpine sh`  