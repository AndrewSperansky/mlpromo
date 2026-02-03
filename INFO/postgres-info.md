Cкачать pgAdmin
https://www.pgadmin.org/download/
Откройте pgAdmin в браузере:
http://localhost:5050

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

`docker exec -it promo_postgres psql -U postgres -d promo`


##  Выйти из длинного вывода  (END - Pager)
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





## Определение директории для логов в контейнере promo_postgres
`docker exec -it promo_postgres cat /etc/postgresql/postgresql.conf | findstr log_directory `   
результат: log_directory = '/var/log/postgresql'




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
`docker exec -it promo_postgres find / -path "/proc" -prune -o -name "postgresql.conf" -print 2>$null`


## Убедиться что promtail пишет новые логи

`docker exec -it promo_promtail sh`
tail -f /var/log/postgresql/postgresql-2025-12-18.log

## Эмуляция медленного запроса (>500 мс)  
SELECT pg_sleep(0.55);  

## Эмуляция ERROR  
SELECT * FROM table_that_does_not_exist;  

## Процессы использующие порт 5432

`netstat -ano | findstr :5432`
 
## Узнаем владельцев процессов

`tasklist /FI "PID eq 6752"`


## Вход в консоль POSTGRES  
`docker exec -it promo_postgres psql -U postgres -d postgres`

## Проверка наличия таблиц

`SELECT tablename FROM pg_tables WHERE schemaname = 'public';`

`SHOW TABLES`

## История миграций
`SELECT * FROM alembic_version;`


## Отладочный аппендикс (1) в env.py

print("=== Таблицы в метаданных ===")
for table in target_metadata.tables:
    print(f"  {table}")
print("=== Конец списка ===")

alembic revision --autogenerate -m "debug_tables"

### Запускаем командой  
`alembic revision --autogenerate -m "test"`

print("\n=== ТАБЛИЦЫ В METADATA (проверка) ===")
for table_name in Base.metadata.tables:
    table = Base.metadata.tables[table_name]
    print(f"  Таблица: {table_name}")
    print(f"  Поля: {list(table.columns.keys())}")
    print(f"    Первичный ключ: {list(table.primary_key)})")
print("=== КОНЕЦ СПИСКА ===")

### Запускаем командой  
`alembic revision --autogenerate -m "debug_tables"`

## 1) Проверка наличия таблиц  
>SELECT tablename 
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('ml_model', 'prediction', 'promo_position');

## 2) Очистить таблицу alembic_version (если она существует):
>DELETE FROM alembic_version;




## Скрипт для консоли Python для проверки подключения к БД

>from sqlalchemy import create_engine, text
>
>url = "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/promo"
engine = create_engine(url)
>
>try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), current_user"))
        db_name, user = result.fetchone()
        print(f"Подключено к БД: {db_name}, пользователь: {user}")
except Exception as e:
    print(f"Ошибка подключения: {e}")


## Подключение  к Postgres в контейнере !!!!!!!!!!!!!!!!
 `docker exec -it promo_postgres psql -U postgres -d promo`

## Посмотреть структуру таблицы
 \d promo
 \d ml_promo
 \d <table_name>
 \dt public.*

## Создание  BACKUP БД
`docker exec -t promo_postgres pg_dump -U postgres promo > backup_$(Get-Date -Format "yyyy-MM-dd_HH-mm").sql`
   

##  📌 Восстановление БД (не сработает если есть битые символы)
docker exec -i promo_postgres psql -U postgres promo < backup_2026-01-14_15-23.sql  


## ШАГ 1. Перекодировать дамп В UTF-8 БЕЗ BOM
### ⚠️ Делать в WSL / Linux, не в Notepad.

`iconv -f UTF-16LE -t UTF-8 backup_2026-01-14_15-23.sql > backup_utf8.sql`


## ШАГ 2. Загрузить перекодированный дамп (bash)
`docker exec -i promo_postgres psql -U postgres -d promo  < backup_utf8.sql`


## Как восстановить БЕЗ ошибок (правильно)
### ✅ Вариант A — самый правильный (рекомендую)

- На Windows:  

`chcp 65001`
`pg_dump -U postgres -d promo --encoding=UTF8 > backup_utf8.sql`

- Потом:  
`docker exec -i promo_postgres psql -U postgres -d promo < backup_utf8.sql`

## Создание дампа внутри контейнера (bush)  на хосте

`docker exec -t promo_postgres   pg_dump -Fc -U postgres promo > backup_before_audit_tables.dump`
docker exec -t promo_postgres   pg_dump -Fc -U postgres promo > promo_ml_backup_before_ml_model_refactor.dump

или

=============================================================  
pg_dump \
  -h localhost \
  -p 5432 \
  -U postgres \
  -d promo \
  -F c \
  -E UTF8 \
  --no-owner \
  --no-privileges \
  -f backup/promo_$(date +%Y%m%d_%H%M).dump

==============================================================

3️⃣ Делаем SQL dump (.sql) — ДЛЯ РЕВЬЮ
pg_dump \
  -h localhost \
  -p 5432 \
  -U postgres \
  -d promo \
  -F p \
  -E UTF8 \
  --no-owner \
  --no-privileges \
  --encoding=UTF8 \
  -f backup/promo_$(date +%Y%m%d_%H%M).sql


## Создание дампа внутри контейнера (bush)  в  контейнере
docker exec -it promo_postgres /bin/bash
pg_dump -U postgres -d promo -Fc -f /tmp/promo_ml_backup_before_ml_model_refactor.dump


### Скопировать дамп на хост
docker cp promo_postgres:/tmp/promo_ml_backup.dump ./promo_ml_backup_before_ml_model_refactor.dump

####  Проверка
 `dir backup_before_audit_tables.dump`  

Дролжно быть: backup_before_audit_tables.dump

🧷 sql
SHOW server_encoding;
SHOW client_encoding;



- docker compose build postgres
- docker compose up -d postgres
- docker compose up -d --force-recreate postgres


## IP‑адрес контейнера (опционально)
`- docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' promo_postgres `

##  Логи
`docker logs promo_postgres --tail=50`

### Проверить строку "DATABASE_URL"
`docker exec -it promo_ml_backend python -c "
from app.core.settings import settings; 
print(settings.ML_DATABASE_URL)
"`  
Должно быть:  
postgresql+psycopg2://postgres:postgres@postgres:5432/promo


## ПРОВЕРКА РАБОТОСПОСОБНОСТИ Postgres

### 0. Базовая картина
docker ps -a
docker compose -f docker-compose.prod.yml ps


Смотрим:

статус promo_postgres

unhealthy vs exited

### 📜 1. Логи (ты уже сделал, но фиксируем стандарт)
docker logs promo_postgres --tail=200


Если надо онлайн:

docker logs -f promo_postgres

### 🧠 2. Проверка env внутри контейнера

Очень важно — часто тут косяк.

`docker inspect promo_postgres --format='{{range .Config.Env}}{{println .}}{{end}}'  `


Ищем:

POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

### 🧪 3. Попробовать залогиниться вручную (внутри контейнера)
`docker exec -it promo_postgres bash`


Внутри:

`psql -U postgres`


или явно:

psql -U postgres -d promo


❌ Если тут password failed → 100% проблема в volume / инициализации
✅ Если зашло → проблема в healthcheck или внешнем клиенте

### 🧱 4. Проверка, не "залип" ли старый volume

Это классика.

docker volume ls
docker volume inspect promo-ml_postgres-data


Если volume создан раньше, чем ты поменял пароль — Postgres его НЕ пересоздаёт.

### 💣 5. Жёсткий, но честный тест (СНОС ДАННЫХ)

⚠️ Делай только если это не prod с данными.

`docker compose -f docker-compose.prod.yml down -v`
`docker compose -f docker-compose.prod.yml up -d`


👉 В 80% случаев это сразу чинит password authentication failed

### 🧬 6. Проверка pg_hba.conf (раз уж он фигурирует в логах)
docker exec -it promo_postgres bash

##### Внутри:

`cat /var/lib/postgresql/data/pg_hba.conf | sed -n '1,200p' `

Ищем:

`host all all all scram-sha-256  `


➡️ это норма, проблема не тут, а в пароле

### 🩺 7. Проверка healthcheck вручную

`docker exec promo_postgres pg_isready -U postgres`

Если тут no response или rejecting connections — контейнер формально жив, но auth сломан.


### 🌐 8. Проверка подключения из другого контейнера (backend)

`docker exec -it promo_ml_backend bash`

Внутри:

`psql -h promo_postgres -U postgres -d promo`

(пароль спросит)

### 🔐 9. Проверка, не подсовывается ли пароль из .env

Get-Content .env
Get-Content .env.prod


И потом:

`docker compose -f docker-compose.prod.yml config`

## Запуск psql внутри контейнера
 docker exec -it promo_postgres bash
 psql -h localhost -U postgres -d promo
 
### Посмотреть содержание settings.DATABASE_URL
`python -c "from app.core.settings import settings; print(settings.DATABASE_URL)"`

Должно быть: postgresql+psycopg2://postgres:postgres@postgres:5432/promo





# WARNING  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Внешний ключ ml_prediction_result_model_id_fkey ссылается на столбец id таблицы ml_model, который имеет тип integer. 
При изменении типа model_id на text возникает конфликт:



### -- 1. Удаляем внешний ключ

ALTER TABLE public.ml_prediction_result 
DROP CONSTRAINT ml_prediction_result_model_id_fkey;

###  -- 2. Меняем тип в дочерней таблице
Для безопасного преобразования integer → text используйте USING:

ALTER TABLE public.ml_prediction_result
ALTER COLUMN model_id TYPE TEXT USING model_id::text;


### -- 3. Меняем тип в родительской таблице
ALTER TABLE public.ml_model
ALTER COLUMN id TYPE TEXT USING id::text;

### -- 4. Восстанавливаем внешний ключ
ALTER TABLE public.ml_prediction_result
ADD CONSTRAINT ml_prediction_result_model_id_fkey
FOREIGN KEY (model_id) REFERENCES ml_model(id);

