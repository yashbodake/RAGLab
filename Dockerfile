# ---- Stage 1: Build Vue 3 Frontend ----
FROM node:20-slim AS frontend-build

WORKDIR /app/frontend

# Install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit

# Build production bundle
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python Backend + Serve ----
FROM python:3.10-slim

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy data files
COPY data/articles.json ./data/articles.json

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist/ ./static/

# Environment variables
ENV HF_HOME=/data/huggingface
ENV CHROMA_PERSIST_PATH=/data/chroma_db
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Create persistent data directory
RUN mkdir -p /data/huggingface /data/chroma_db

# Expose port (required by HF Spaces)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
