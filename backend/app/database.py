from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import get_settings


def normalize_database_url(url: str) -> str:
    # Managed Postgres providers (Render included) typically hand out bare postgres:// or
    # postgresql:// URLs, which SQLAlchemy resolves to the classic psycopg2 driver by default.
    # This project only installs psycopg3 (requirements.txt: psycopg[binary]), so an
    # unnormalized URL would crash on startup with ModuleNotFoundError: psycopg2. Force the
    # psycopg3 dialect unless a driver is already specified, or it's SQLite.
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


settings = get_settings()
database_url = normalize_database_url(settings.database_url)
engine_kwargs = {"connect_args": {"check_same_thread": False}} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, pool_pre_ping=True, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
