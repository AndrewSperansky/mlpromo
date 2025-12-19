## Перезапуск PostgreSQL после изменений в postgresql.conf
docker compose up -d --force-recreate postgres

## Прочитать последние 50 логов
docker logs promo_postgres --tail 50

## Проверка что параметр (в postgresql.conf) реально применился

`docker exec -it promo_postgres psql -U postgres -d promo`
`SHOW log_min_duration_statement;`


## 🔍 Проверка, что конфиг подхватился после монтирования ./docker/postgres/postgresql.conf

`docker exec -it promo_postgres psql -U promo -d promo`

`SHOW config_file;`  
`SHOW log_min_duration_statement;  `
`SHOW shared_preload_libraries;  `

Должно быть:
/etc/postgresql/postgresql.conf

## 🧠 ВАЖНО (из практики)

❗ НЕ редактируй /var/lib/postgresql/data/postgresql.conf напрямую
— при пересоздании контейнера ты всё потеряешь.

### Заходим под системным пользователем postgres

docker exec -it promo_postgres psql -U postgres  

## Смотрим, какие роли вообще есть

`\du`


## Создаём пользователя и БД (ПРАВИЛЬНО)

>CREATE ROLE promo WITH  
  LOGIN  
  PASSWORD 'promo';  
CREATE DATABASE promo  
  OWNER promo;  
GRANT ALL PRIVILEGES ON DATABASE promo TO promo;


### Проверка:
`\du`
`\l`


## Проверяем подключение как promo  
`docker exec -it promo_postgres psql -U promo -d promo`

## 🔎 Проверим владельца базы (важно)

#### В psql:
`\l`

## ✅ Исправляем владельца (рекомендую)
`ALTER DATABASE promo OWNER TO promo;  `

### Проверка:  
`\l`

### Выходим из psql:
`\q`

### пробуем:

`docker exec -it promo_postgres psql -U promo -d promo`

### Если зашёл — идеально ✔️


##  Выйти из длинного вывода (END)
`q` без Enter

## 🛠 Как вообще отключить pager (чтобы больше не бесило)
### 🔹 В текущей сессии: 

`\pset pager off`

### 🔹 Навсегда (рекомендую):

`\setenv PAGER off`

### 🔹 или при запуске:

`docker exec -it promo_postgres psql -U postgres -P pager=off`

## Проверить метрики


`curl http://localhost:9187/metrics | findstr pg_stat`


## Войти в консоль postgres  

`docker exec -it promo_postgres psql -U postgres -d promo`



docker inspect promo_postgres --format='OOMKilled={{.State.OOMKilled}} ExitCode={{.State.ExitCode}}'


## Прочитать логи в контейнере promo_grafana

`docker exec -it --user root promo_grafana sh`            
wget -qO- "http://loki:3100/loki/api/v1/query_range?query={job=\"postgres\"}&limit=5"


## Определение директории для логов в контейнере promo_postgres
`docker exec -it promo_postgres cat /etc/postgresql/postgresql.conf | findstr log_directory `   
результат: log_directory = '/var/log/postgresql'


## Прочитать логи в контейнере promtail

`docker exec -it promo_promtail sh`  

### Видит ли promtail нужные файлы  
`ls -la /var/log/postgresql/`  

### Вручную прочитать логи
`cat /var/log/postgresql/postgresql-*.log`  
`cat /var/log/postgresql/postgresql-*.log | tail -n 5`

### Если ошибка Permission denied — исправьте права в контейнере PostgreSQL:  
`docker exec -it promo_postgres chmod 644 /var/log/postgresql/postgresql-*.log`

>Почему 644?  
6 (владелец): чтение + запись.  
4 (группа): только чтение.  
4 (остальные): только чтение. 


## Найти путь к файлу postgresql.conf в контейнере promo_postgres
docker exec -it promo_postgres find / -path "/proc" -prune -o -name "postgresql.conf" -print 2>$null


## Убедиться что promtail пишет новые логи

docker exec -it promo_promtail sh
tail -f /var/log/postgresql/postgresql-2025-12-18.log

## Эмуляция медленного запроса (>500 мс)  
SELECT pg_sleep(0.55);  

## Эмуляция ERROR  
SELECT * FROM table_that_does_not_exist;  





