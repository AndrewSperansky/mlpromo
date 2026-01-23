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