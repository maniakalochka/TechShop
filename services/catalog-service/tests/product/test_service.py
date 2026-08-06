import pytest
from catalog_service.product.service import ProductService


class MockProductRepository:
    def __init__(self):
        self.products = {}

    async def create_product(self, product_data):
        self.products[product_data.id] = product_data
        return product_data

    async def get_product_by_id(self, product_id):
        return self.products.get(product_id)


@pytest.mark.asyncio
async def test_create_product(product_factory):
    # Arrange
    mock_repo = MockProductRepository()
    service = ProductService(mock_repo)
    product_data = product_factory()

    # Act
    created_product = await service.create_product(product_data)

    # Assert
    assert created_product == product_data
    assert mock_repo.products[product_data.id] == product_data


@pytest.mark.asyncio
async def test_get_product(product_factory):
    # Arrange
    mock_repo = MockProductRepository()
    service = ProductService(mock_repo)
    product_data = product_factory()
    await mock_repo.create_product(product_data)

    # Act
    retrieved_product = await service.get_product(product_data.id)

    # Assert
    assert retrieved_product == product_data
