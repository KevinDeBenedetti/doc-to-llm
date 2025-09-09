FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock
RUN uv sync --no-cache && uv cache clean

COPY app /app/app

ENV PYTHONPATH=/app

# CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload"]
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]