import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def resolve_database_url() -> str:
    """Resolve a direct URL or a mounted secret-file URL."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    database_url_file = os.getenv("DATABASE_URL_FILE")
    if database_url_file:
        with open(database_url_file, encoding="utf-8") as secret_file:
            return secret_file.read().strip()
    return "sqlite:///./tidewatch.db"


DATABASE_URL = resolve_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
