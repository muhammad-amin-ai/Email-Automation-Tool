import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings


def ensure_database_exists(
    host: str, port: int, user: str, password: str, db_name: str
) -> None:
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset="utf8mb4",
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()


ensure_database_exists(
    settings.DB_HOST,
    settings.DB_PORT,
    settings.DB_USER,
    settings.DB_PASSWORD,
    settings.DB_NAME,
)

DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
