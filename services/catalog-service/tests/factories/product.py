import datetime

import factory
from catalog_service.product.model import Product


class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    id = factory.Faker("uuid4")
    name = factory.Sequence(lambda n: f"Product {n}")
    description = "The latest gaming console from Sony."
    price = 499.99
    quantity = 100
    created_date = factory.LazyFunction(datetime.datetime.now)
    updated_date = factory.LazyFunction(datetime.datetime.now)
