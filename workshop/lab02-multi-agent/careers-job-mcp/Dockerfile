FROM python:3.12.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    CAREERS_HOST=0.0.0.0 \
    CAREERS_PORT=8080 \
    CAREERS_DB_PATH=/app/data/careers-jobs.sqlite3

WORKDIR /app

COPY requirements.txt .
COPY .wheelhouse ./wheelhouse
RUN if find wheelhouse -type f -name '*.whl' | grep -q .; then \
        pip install --no-cache-dir --no-index --find-links=wheelhouse --requirement requirements.txt; \
    else \
        pip install --no-cache-dir --requirement requirements.txt; \
    fi \
    && rm -rf wheelhouse \
    && groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app app

COPY --chown=app:app src ./src
COPY --chown=app:app data ./data

USER app
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2).read()"]

CMD ["python", "-m", "careers_job_mcp"]
