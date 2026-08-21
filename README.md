# TechShop

TechShop is a portfolio microservice backend for an online electronics store. The repository currently contains the `catalog-service`, which owns product and category data.

## Stack

- Python 3.13 and uv
- FastAPI, Pydantic 2, SQLAlchemy 2 (async)
- PostgreSQL 17 and Alembic
- Docker Compose, pytest, Ruff and mypy

## Run locally

1. Create local configuration: `cp .env.example .env`.
2. Start the service and its database:

   ```bash
   docker compose --env-file .env -f infrastructure/docker-compose.yaml up --build
   ```

3. Open `http://localhost:8000/docs`. Liveness is available at `GET /health`; readiness, including a database probe, is `GET /ready`.

The `catalog-migrator` container applies all Alembic migrations before the API starts.

## API

Products and categories expose the same CRUD shape:

| Operation | Category | Product |
| --- | --- | --- |
| Create | `POST /categories` | `POST /products` |
| List | `GET /categories?limit=20&offset=0` | `GET /products?limit=20&offset=0` |
| Read | `GET /categories/{id}` | `GET /products/{id}` |
| Update | `PATCH /categories/{id}` | `PATCH /products/{id}` |
| Delete | `DELETE /categories/{id}` | `DELETE /products/{id}` |

A product requires an existing `category_id`. Prices are positive decimals with at most two fractional digits; quantities cannot be negative. List endpoints are ordered by name and support `limit` from 1 through 100 and a non-negative `offset`.

## Development checks

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
```

Run the database-backed test workflow in isolated containers:

```bash
docker compose -f infrastructure/docker-compose.test.yaml up --build --abort-on-container-exit
docker compose -f infrastructure/docker-compose.test.yaml down -v
```

Install Git hooks once with `uv run pre-commit install`. GitHub Actions runs formatting, linting, type checks and tests on pushes to `main` and pull requests.

## Architecture direction

The next bounded service should be `inventory-service`, responsible for stock and reservations. It should communicate with the future `order-service` through explicit domain events, using FastStream with RabbitMQ or Kafka only once such an integration exists. Services must own their own data and must not write directly to another service's database.
