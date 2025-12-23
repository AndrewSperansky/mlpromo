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

docker inspect -f "{{.State.Status}}" promo_grafana
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}" | Select-String "grafana"

## 50 последних логов Grafana
docker logs promo_grafana --tail 50

## Перезапуск Grafana

docker compose up -d --force-recreate grafana   

## Вход в контейнер promo-grafana

docker exec -it promo_grafana sh

## Grafana:

👉 http://localhost:3000

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
chmod -R 755 /loki
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


## 5️⃣ Обязательные действия после правки

### Выполнить строго в этом порядке:

`docker compose down grafana`  
`docker volume rm promo-ml_grafana-data`      
`ВАЖНО: чтобы UID не кешировался` 
### ⚠️ Если volume не удалить — Grafana может оставить старый autogenerated UID.  
`docker compose up -d grafana`  

## Пересборка контейнера после изменения конфигов в папке docker/grafana/

docker compose up -d --force-recreate grafana
docker restart promo_grafana

## Restart контейнера Grafana (не reload)
### Например, изменение файлов в provisioning
`docker compose restart grafana`
`docker compose up -d --force-recreate grafana`

### Проверка, что provisioning отработал

`docker logs promo_grafana --tail 50`


### 6️⃣ Проверка, что всё починилось (Увидеть настройки)

#### Проверка через API  
##### bash:  
curl http://localhost:3000/api/datasources | grep loki
##### win shell:  
curl http://localhost:3000/api/datasources | Select-String loki
curl http://localhost:3000/api/datasources | sls loki  
curl http://localhost:3000/api/datasources | ConvertFrom-Json

curl -u admin:admin http://localhost:3000/api/datasources

## Из контейнера Grafana
docker exec -it --user root promo_grafana sh  
apk add curl  
curl -u admin:admin http://localhost:3000/api/datasources

#### Ожидаемо:

`"uid": "loki"`


## Проверка promtail   
`docker logs promo_ml_backend --tail 100`

## Пересборка Loki, promtail, grafana после внесения изменений

`docker compose down`
`docker compose up -d --force-recreate promtail loki grafana`

## Grafana
### Правило должно быть ЛИБО:

>`alert + expr + for (Prometheus-совместимый стиль)`  
ЛИБО  
`data + model + condition (Unified Alerting)`

## Проверка сетей для контейнеров (должны быть одинаковые)

`docker inspect promo_grafana promo_prometheus --format='{{.Name}} -> {{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'`

## Проверяем, что Loki реально принимает логи    
### Проверка изнутри контейнера Grafana

`docker exec -it promo_grafana sh`  
`wget -qO- "http://loki:3100/loki/api/v1/labels"`

Если 
{"status":"success","data":["filename","job","levelname","logger","service"]}  
>— Loki работает корректно.
✅ Loki жив
✅ Grafana ↔ Loki связаны
✅ Promtail успешно пишет логи

## Проверяем, есть ли сами записи логов  
### Прямой запрос логов backend

`exec -it promo_grafana sh`
`wget -qO- "http://loki:3100/loki/api/v1/query_range?query={job=\"promo_ml_backend\"}&limit=5"`

>👉 Ответ пустой = Loki жив, но логов с job="promo_ml_backend" в хранилище НЕТ.
>Значит:
>Grafana ❌ не виновата
>Loki ❌ не виноват
>Dashboard ❌ не виноват
>Проблема строго между backend → promtail → loki.

## Проверяем: Promtail вообще читает файлы?  
### Проверка targets Promtail

`docker exec -it promo_promtail wget -qO- http://localhost:9080/targets`

## Проверка файла как он есть в конфигурации
`docker exec promo_promtail cat /etc/promtail/promtail-config.yml`


docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

## Проверьте доступность Loki из контейнера Promtail:
docker exec promo_promtail curl -v http://promo_loki:3100/ready


