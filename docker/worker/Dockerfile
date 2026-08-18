# =============================================================================
# Worker image — same env as backend but runs Celery instead of uvicorn
# =============================================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 libxext6 libxrender1 libgl1 libglib2.0-0 \
    libpq-dev gcc curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Les scripts installés (celery, uvicorn) mettent leur propre dossier en tête de
# sys.path, pas le répertoire courant : sans PYTHONPATH, `import shared` échoue.
ENV PYTHONPATH=/app

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt && \
    pip install "sqlalchemy[asyncio]" asyncpg alembic \
                "python-jose[cryptography]" "passlib[bcrypt]" bcrypt \
                httpx redis celery opencv-python-headless numpy \
                pydantic pydantic-settings

COPY backend/ /app/
COPY shared/ /app/shared/
COPY video_engine/ /app/video_engine/
COPY ai_engine/ /app/ai_engine/
COPY workers/ /app/worker/

RUN mkdir -p /app/data/uploads /app/data/temp /app/data/outputs /app/data/logs

CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=INFO", "-Q", "clips,video,ai", "--concurrency=2"]
