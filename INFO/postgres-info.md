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