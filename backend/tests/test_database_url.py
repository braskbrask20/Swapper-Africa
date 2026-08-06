from app.database import normalize_database_url


def test_normalizes_bare_postgres_scheme():
    assert normalize_database_url("postgres://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_normalizes_bare_postgresql_scheme():
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"


def test_leaves_already_prefixed_url_alone():
    url = "postgresql+psycopg://user:pass@host/db"
    assert normalize_database_url(url) == url


def test_leaves_sqlite_url_alone():
    url = "sqlite:///./swapper.db"
    assert normalize_database_url(url) == url
