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