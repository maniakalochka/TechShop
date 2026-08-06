import pytest
from tests.factories.product import ProductFactory


@pytest.fixture
def product_factory():
    return ProductFactory
