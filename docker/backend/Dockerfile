# =============================================================================
# Backend image — Python 3.11 + ffmpeg + opencv + AI deps
# =============================================================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System dependencies: ffmpeg, libgl, build tools, postgres client
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    libglib2.0-0 \
    libpq-dev \
    gcc \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Les scripts installés (celery, uvicorn) mettent leur propre dossier en tête de
# sys.path, pas le répertoire courant : sans PYTHONPATH, `import shared` échoue.
ENV PYTHONPATH=/app

WORKDIR /app

# Install Python deps first for layer caching
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt && \
    pip install "fastapi[standard]" "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg alembic \
                "python-jose[cryptography]" "passlib[bcrypt]" bcrypt python-multipart \
                httpx redis celery opencv-python-headless numpy \
                pydantic pydantic-settings

# Copy source
COPY backend/ /app/
COPY shared/ /app/shared/
COPY video_engine/ /app/video_engine/
COPY ai_engine/ /app/ai_engine/
COPY database/ /app/database/
COPY workers/ /app/worker/

# Create data dirs
RUN mkdir -p /app/data/uploads /app/data/temp /app/data/outputs /app/data/logs

EXPOSE 8000

# Default: run migrations then start uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
