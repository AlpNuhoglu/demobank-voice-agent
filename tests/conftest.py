from collections.abc import Iterator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.config import TIMEZONE
from app.db import make_engine

# Fixed reference time for deterministic tests. Production seeding uses the real clock.
REFERENCE_NOW = datetime(2026, 10, 1, 12, 0, tzinfo=TIMEZONE)


@pytest.fixture
def engine(tmp_path) -> Iterator[Engine]:
    eng = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    yield eng
    eng.dispose()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    from app.main import create_app

    with TestClient(create_app(engine)) as c:
        yield c
