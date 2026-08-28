import uuid
from decimal import Decimal

from catalog_service.category.dependencies import get_category_service
from catalog_service.category.model import Category
from catalog_service.category.service import CategoryAlreadyExistsError
from catalog_service.main import app
from catalog_service.product.dependencies import get_product_service
from catalog_service.product.model import Product
from catalog_service.product.service import CategoryNotFoundError
from fastapi.testclient import TestClient


class FakeCategoryService:
    def __init__(self) -> None:
        self.category = Category(id=uuid.uuid4(), name="Gaming", description="Games")

    async def create_category(self, payload):  # type: ignore[no-untyped-def]
        if payload.name == self.category.name:
            raise CategoryAlreadyExistsError
        return Category(id=uuid.uuid4(), name=payload.name, description=payload.description)

    async def list_categories(self, *, limit: int, offset: int):  # type: ignore[no-untyped-def]
        return [self.category][offset : offset + limit]

    async def get_category_by_id(self, category_id: uuid.UUID):  # type: ignore[no-untyped-def]
        return self.category if category_id == self.category.id else None

    async def update_category(self, category_id: uuid.UUID, payload):  # type: ignore[no-untyped-def]
        return self.category if category_id == self.category.id else None

    async def delete_category(self, category_id: uuid.UUID) -> bool:
        return category_id == self.category.id


class FakeProductService:
    def __init__(self, category_id: uuid.UUID) -> None:
        self.product = Product(
            id=uuid.uuid4(),
            name="Console",
            description="Current generation console",
            price=Decimal("499.99"),
            category_id=category_id,
        )

    async def create_product(self, payload):  # type: ignore[no-untyped-def]
        if payload.category_id != self.product.category_id:
            raise CategoryNotFoundError
        return self.product

    async def list(self, *, limit: int, offset: int):  # type: ignore[no-untyped-def]
        return [self.product][offset : offset + limit]

    async def get_product(self, product_id: uuid.UUID):  # type: ignore[no-untyped-def]
        return self.product if product_id == self.product.id else None

    async def update_product(self, product_id: uuid.UUID, payload):  # type: ignore[no-untyped-def]
        return self.product if product_id == self.product.id else None

    async def delete_product(self, product_id: uuid.UUID) -> bool:
        return product_id == self.product.id


def test_category_api_returns_created_resource_and_404(client: TestClient) -> None:
    service = FakeCategoryService()

    app.dependency_overrides[get_category_service] = lambda: service

    created = client.post("/categories", json={"name": "Audio", "description": "Headphones"})
    missing = client.get(f"/categories/{uuid.uuid4()}")

    assert created.status_code == 201
    assert created.json()["name"] == "Audio"
    assert missing.status_code == 404


def test_product_api_validates_and_paginates(client: TestClient) -> None:
    category_service = FakeCategoryService()
    product_service = FakeProductService(category_service.category.id)

    app.dependency_overrides[get_category_service] = lambda: category_service
    app.dependency_overrides[get_product_service] = lambda: product_service

    invalid = client.post(
        "/products",
        json={
            "name": "Console",
            "price": "0",
            "category_id": str(category_service.category.id),
        },
    )
    created = client.post(
        "/products",
        json={
            "name": "Console",
            "price": "499.99",
            "category_id": str(category_service.category.id),
        },
    )
    missing_category = client.post(
        "/products",
        json={
            "name": "Console",
            "price": "499.99",
            "category_id": str(uuid.uuid4()),
        },
    )
    listed = client.get("/products?limit=1&offset=0")
    missing = client.get(f"/products/{uuid.uuid4()}")

    assert invalid.status_code == 422
    assert created.status_code == 201
    assert missing_category.status_code == 404
    assert listed.status_code == 200
    assert listed.json()[0]["price"] == "499.99"
    assert missing.status_code == 404
