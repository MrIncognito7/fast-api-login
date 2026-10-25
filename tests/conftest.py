import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import pytest
from fastapi.testclient import TestClient

from app.database import engine
from app.main import app
from app.models import Base
from app.routers.auth import limiter
from app.routers.sendmail import _sent_otps  # type: ignore


@pytest.fixture()
def client():
    # Reset tables through the existing engine/connection pool rather than
    # deleting the sqlite file out from under it — deleting the file while
    # the pool holds pooled connections to it can leave the pool pointing at
    # a stale/unlinked file handle and raise spurious "readonly database"
    # errors on the next test.
    Base.metadata.drop_all(bind=engine)

    # Rate limits (e.g. 3/minute on /register) are tracked in an in-memory
    # store that otherwise persists across tests in the same process.
    limiter.reset()

    with TestClient(app) as c:
        yield c


def pytest_sessionfinish(session, exitstatus):
    db_path = "./test.db"
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(autouse=True)
def clear_sent_otps():
    _sent_otps.clear()
    yield
    _sent_otps.clear()
