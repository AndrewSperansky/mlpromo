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
`docker exec -it promo_postgres find / -path "/proc" -prune -o -name "postgresql.conf" -print 2>$null`


## Убедиться что promtail пишет новые логи

`docker exec -it promo_promtail sh`
tail -f /var/log/postgresql/postgresql-2025-12-18.log

## Эмуляция медленного запроса (>500 мс)  
SELECT pg_sleep(0.55);  

## Эмуляция ERROR  
SELECT * FROM table_that_does_not_exist;  



# ORM

## Инициализация Alembic в проекте
`python -m alembic init migrations`

В корне проекта появится:

>alembic.ini
>migrations/
  ├─ env.py
  ├─ script.py.mako
  └─ versions/
> 

## 📦 Миграция alembic
`alembic revision --autogenerate`  
`python -m alembic revision --autogenerate -m "initial models with mixins"`
вместе с
## 📦 Применение миграции

`alembic upgrade head`   — выполняет миграции, но может молча пропускать ошибки (например, если таблица уже существует).
`alembic --raiseerr upgrade head`   — обязательно прерывает выполнение при любой ошибке и выводит детальный лог.
 !!!! alembic stamp head   -- очень, очень редко. Лучше не использовать (только все путает)
→ БД меняется
→ в таблице alembic_version фиксируется версия
`alembic --debug upgrade 99d37dda7ea0`

## 📦 Миграция под миксины
`alembic revision --autogenerate -m "create initial models with mixins"`

## 📦 Создать миграцию вручную

`alembic revision --autogenerate -m "initial"`

## Удалить пустую миграцию
`del migrations\versions\f85b934f5c57_initial_models_with_mixins.py`

## История миграций
`alembic history` 

## Откат до версии
`alembic downgrade 99d37dda7ea0`



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
     