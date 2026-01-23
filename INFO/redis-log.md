



`docker logs promo_promtail --tail 50`  
`docker exec promo_redis ls -la /var/log/redis/`  

## 1) Существование файла логов Redis     
`docker exec promo_redis ls -la /var/log/redis/`



## 2) Убедиться, что Redis использует наш конфиг
## Проверить, что Redis запущен с нужным конфигом:

bash
`docker exec promo_redis ps aux | grep redis-server`

`docker exec promo_redis ps aux | findstr redis-server`

## 3) Проверьте содержимое конфига внутри контейнера  
 
`docker exec promo_redis cat /usr/local/etc/redis/redis.conf | grep logfile`  
`docker exec promo_redis cat /usr/local/etc/redis/redis.conf | findstr logfile`

## 4) Проверьте права на запись в /var/log/redis
### Redis должен иметь доступ к директории:

bash
`docker exec promo_redis touch /var/log/redis/test.log && echo "OK" || echo "FAIL"`
Если выводится FAIL — проблема с правами.

## 5. Проверьте логи Redis на ошибки
### Посмотрите, нет ли ошибок при запуске:

bash
`docker logs promo_redis | grep -i error`
`docker logs promo_redis | findstr -i error`


## 6. Создание файлов логов (если его нет) вручную
### Если файл отсутствует, попробуйте создать его вручную:

bash
`docker exec promo_redis mkdir -p /var/log/redis`
`docker exec promo_redis touch /var/log/redis/redis.log`
`docker exec promo_redis chown redis:redis /var/log/redis/redis.log`

### После создания файлов перезапуск promo_redis
`docker restart promo_redis`


## 7. Проверьте Promtail после перезапуска  
### Перезапустите Promtail, чтобы он перечитал файл:

bash
`docker restart promo_promtail`

### После этого проверьте его логи:

bash
`docker logs promo_promtail | grep redis`


# Если проблема сохраняется  
## Проверьте volume redis-logs  
### Убедитесь, что volume создан и подключен:

bash
`docker volume inspect redis-logs`
Если volume отсутствует — пересоздайте его:

bash
`docker volume create redis-logs`
`docker-compose down && docker-compose up -d`

### Попробуйте другой путь для логов
### В redis.conf измените путь на /data/redis.log:

conf
logfile /data/redis.log
### В docker-compose.yml добавьте volume:

>yaml
redis:
  volumes:
    - redis-data:/data
    - ./docker/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro


## 🧯 КАК ПРАВИЛЬНО ПРИМЕНИТЬ ИЗМЕНЕНИЯ после schema-error
### Важно: после schema-error нужен чистый старт.

`docker compose stop promtail`
`docker compose up -d promtail`



`docker exec -it promo_redis chmod 755 /data`

`docker exec -it promo_redis tail -n 5 /data/redis.log`


## Realtime logs
`docker logs --tail 0 -f promo_promtail`
`docker logs --tail 10 -f promo_promtail`



Узнаем ID у promo_redis
 docker inspect -f '{{.Id}}' promo_redis
f915e5cee0c8bd3a6bb1453cde1a880b37a6a06d6198f9be9c495494cc9a8833


## Скопировать promtail-config.yml в контейнер promo_promtail из хоста

docker cp D:\PycharmProjects\promo-ml\docker\promtail\promtail-config.yml promo_promtail:/etc/promtail/config.yml

## Проверить, что файл promtail-config.yml попал в контейнер
bash
docker exec promo_promtail cat /etc/promtail/config.yml


Целевой файл логов найден
key="/var/lib/docker/containers/*/*-json.log:{container_name=\"promo_redis\", job=\"redis\", service=\"redis\"}"

## Посмотреть логи в контейнере redis

docker logs promo_redis --tail 10
1:M 23 Dec 2025 08:47:46.126 * <search> Loading event starts
1:M 23 Dec 2025 08:47:46.126 * <search> Enabled workers threadpool of size 4
1:M 23 Dec 2025 08:47:46.126 * Loading RDB produced by version 8.2.2
1:M 23 Dec 2025 08:47:46.126 * RDB age 3 seconds
1:M 23 Dec 2025 08:47:46.126 * RDB memory usage when created 0.94 Mb
1:M 23 Dec 2025 08:47:46.126 * Done loading RDB, keys loaded: 0, keys expired: 0.
1:M 23 Dec 2025 08:47:46.126 * <search> Disabled workers threadpool of size 4
1:M 23 Dec 2025 08:47:46.126 * <search> Loading event ends
1:M 23 Dec 2025 08:47:46.126 * DB loaded from disk: 0.000 seconds
1:M 23 Dec 2025 08:47:46.127 * Ready to accept connections tcp

Найти реальный путь к логам redis

docker inspect promo_redis | grep LogPath


## найти актуальные логи контейнеров — попробуйте эту команду:

bash
docker inspect --format='{{.LogPath}}' $(docker ps -q)