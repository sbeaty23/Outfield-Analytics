FROM python:3.13-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY pyproject.toml ./
COPY app ./app
RUN pip install --prefix=/install .

FROM builder AS test

RUN pip install ".[test]"
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY tests ./tests
RUN pytest --quiet

FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --no-create-home app

COPY --from=builder /install /usr/local
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f\"http://localhost:{os.environ['BACKEND_PORT']}/api/health\", timeout=2)"]

CMD ["sh", "-c", "exec python -m uvicorn app.main:app --no-access-log --host \"$BACKEND_HOST\" --port \"$BACKEND_PORT\""]
