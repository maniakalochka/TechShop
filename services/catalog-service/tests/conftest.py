import uuid
from collections.abc import Generator

import pytest
from catalog_service.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Generator[TestClient]:
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def category_id() -> uuid.UUID:
    return uuid.uuid4()
