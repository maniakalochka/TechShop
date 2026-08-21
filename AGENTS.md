# AGENTS.md

## Project

This repository contains a microservice-based backend for an online electronics store.

The project is used as a portfolio/interview project, so code quality, architecture,
testability, typing, and maintainability are important.

## Tech Stack

Use the following technologies:

- Python 3.13
- uv
- FastAPI
- SQLAlchemy 2.x
- Pydantic 2.x
- pytest
- FastStream
- PostgreSQL
- Redis
- RabbitMQ
- Apache Kafka
- Docker / Docker Compose

Do not introduce alternative frameworks or infrastructure without explicit approval.

## Package Management

Use `uv` for dependency management and command execution.

Prefer:

```bash
uv sync
uv add <package>
uv add --dev <package>
uv run <command>
