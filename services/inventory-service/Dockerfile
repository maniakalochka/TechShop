FROM python:3.13-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
ARG INSTALL_DEV=false
RUN if [ "$INSTALL_DEV" = "true" ]; then uv sync --frozen; else uv sync --frozen --no-dev; fi
COPY packages/contracts ./packages/contracts
COPY services/inventory-service ./services/inventory-service
ENV PYTHONPATH=/app/packages/contracts/src:/app/services/inventory-service/src
WORKDIR /app/services/inventory-service
ENTRYPOINT ["uv", "run", "uvicorn"]
CMD ["inventory_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
