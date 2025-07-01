# STAGE 1: Build dependencies
FROM python:3.11 as builder

RUN pip install "poetry>=1.5"

WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN python -m poetry self add poetry-plugin-export && \
    python -m poetry export -f requirements.txt --output requirements.txt --without-hashes


# STAGE 2: Production image
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends libmagic1 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/output/text /app/output/images \
    && chown -R appuser:appuser /app/output

COPY --chown=appuser:appuser mymeet_scraper/ ./mymeet_scraper/

USER appuser

ENTRYPOINT ["python", "-m", "mymeet_scraper.main"]