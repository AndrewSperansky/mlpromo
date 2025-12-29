# db/session.py
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/promo"
#postgresql+psycopg2://<user>:<password>@<host>:<port>/<dbname>

engine = create_engine(
    settings.database_url,
    echo=settings.sqlalchemy_echo,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()