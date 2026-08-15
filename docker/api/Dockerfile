FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/docker

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
COPY packages/core/pyproject.toml ./packages/core/
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/worker/pyproject.toml ./apps/worker/
RUN uv sync --frozen --no-install-workspace --group live

COPY packages/core ./packages/core
COPY apps/api ./apps/api
RUN uv sync --frozen --group live

ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/apps/api
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
