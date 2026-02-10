## Проверяем, есть ли вообще лог NGINX


`docker exec -it promo_nginx ls -l /var/log/nginx`

`docker exec -it promo_nginx tail -n 5 /var/log/nginx/access.log`

http://localhost:8000/   --> {"status":"ok","service":"promo-ml"}  

и сразу  
`docker exec -it promo_nginx sh -c "tail -n 3 /var/log/nginx/access.json"`

Если access.log пуст → nginx не пишет туда


## Чиним права (как с Postgres)
`docker exec -it promo_nginx chown nginx:nginx /var/log/nginx/access.json`
`docker exec -it promo_nginx chmod 644 /var/log/nginx/access.json`

## Контроль: файл живой?
`docker exec -it promo_nginx sh -c "tail -f /var/log/nginx/access.json"`



🧭 Docker + NGINX — все рабочие команды

Контейнер у нас:

promo_nginx

🚀 Запуск / остановка
▶ Запустить nginx
`docker compose up -d nginx `

⏹ Остановить nginx  
`docker compose stop nginx `  

🔄 Перезапуск nginx  
`docker compose restart nginx`

❌ Удалить контейнер nginx  
`docker compose rm -f nginx`  

🔍 Статус и диагностика
📦 Проверить, что контейнер жив  
`docker ps | grep promo_nginx`  

🩺 Healthcheck  
`docker inspect promo_nginx --format='{{.State.Health.Status}}'  `


Ожидаем:  healthy

📜 Логи (очень часто нужно)
📄 Последние 50 строк
`docker logs promo_nginx --tail=50`

🔁 Логи в реальном времени
`docker logs -f promo_nginx`

🧠 Внутрь контейнера
🔑 Зайти внутрь nginx
`docker exec -it promo_nginx /bin/sh`


(nginx обычно alpine → /bin/sh, не bash)

🔍 Проверить конфиг внутри контейнера
`cat /etc/nginx/nginx.conf`

🔄 Перечитать конфиг nginx БЕЗ перезапуска контейнера

(очень крутая фича)

`docker exec promo_nginx nginx -s reload`


Если конфиг битый — nginx скажет сразу.

🧪 Проверка конфига nginx
`docker exec promo_nginx nginx -t`


Ожидаем:   
syntax is ok
test is successful

🌐 Проверка портов
Проверка, что nginx слушает  
`docker exec promo_nginx netstat -tulpn`


или

docker exec promo_nginx ss -ltnp

🧹 Полная пересборка nginx (если меняли конфиг/образ)  
`docker compose build nginx`  
`docker compose up -d nginx`

🚨 Если nginx умер (быстро восстановить)
`docker compose down nginx`  
`docker compose up -d nginx`  


или жёстко:

`docker rm -f promo_nginx`    
`docker compose up -d nginx`  


🧠 PROD-памятка (важно)

✔ nginx никогда не пишет код
✔ конфиг — всегда volume
✔ reload > restart
✔ healthcheck = must have
✔ если backend unhealthy → nginx стартует, но отдаёт 502
