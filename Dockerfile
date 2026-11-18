# ========================================================
# super_ai_editor - Multi-Platform Dockerfile
# Works seamlessly on macOS (Apple Silicon & Intel) and Windows 10/11
# ========================================================

FROM python:3.11-slim-bookworm

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Install FFmpeg and audio processing utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python backend dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt || true

# Copy entire application code
COPY backend /app/backend
COPY frontend/dist /app/frontend/dist

# Pre-generate RealSFX sound library at build time
RUN python3 -c "import sys; sys.path.insert(0, '/app'); from backend.app.services.realsfx_service import ensure_default_sfx_library; ensure_default_sfx_library()"

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

EXPOSE 8000

CMD ["python3", "backend/run.py"]
