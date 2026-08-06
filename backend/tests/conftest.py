import os
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_swapper.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["ENVIRONMENT"] = "development"
os.environ["JWT_SECRET"] = "test-only-secret"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:8000"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "test-admin-password-1234"

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

import pytest
from fastapi.testclient import TestClient

from app.main import app, reset_rate_limits


@pytest.fixture()
def client():
    reset_rate_limits()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def _cleanup_db():
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
