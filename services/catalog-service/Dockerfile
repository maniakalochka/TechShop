FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY services/catalog-service ./services/catalog-service

ENV PYTHONPATH=/app/services/catalog-service/src

WORKDIR /app/services/catalog-service

ENTRYPOINT ["uv", "run", "uvicorn"]
CMD ["catalog_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
