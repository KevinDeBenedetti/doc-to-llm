FROM python:3.13-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

RUN uv sync --no-cache

COPY main.py /app/main.py
COPY src/ /app/src

ENV PYTHONPATH=/app

FROM base AS dev
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--reload"]