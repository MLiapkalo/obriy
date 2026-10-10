FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

COPY uv.lock pyproject.toml ./
COPY services/api/pyproject.toml services/api/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --package obriy-api --no-install-workspace

COPY services/api/src services/api/src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --package obriy-api

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health/live')"
CMD ["uvicorn", "--factory", "obriy_api.main:create_app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
