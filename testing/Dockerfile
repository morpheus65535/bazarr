# Bazarr Test Build - feature/parallel-tasks-setting
# This Dockerfile builds a complete Bazarr image for testing the parallel tasks feature

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files first for better caching
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy frontend source files
COPY frontend/ .

# Build the frontend
RUN npm run build

# Stage 2: Final Image
FROM alpine:3.22

LABEL maintainer="Bazarr Testing"
LABEL description="Test build for parallel-tasks-setting feature branch"

# Install build dependencies and runtime dependencies
RUN \
  apk add --no-cache --virtual=build-dependencies \
    build-base \
    cargo \
    libffi-dev \
    libpq-dev \
    libxml2-dev \
    libxslt-dev \
    python3-dev && \
  apk add --no-cache \
    ffmpeg \
    libxml2 \
    libxslt \
    mediainfo \
    python3 \
    py3-pip \
    p7zip \
    bash \
    curl && \
  mkdir -p \
    /app/bazarr/bin \
    /config

# Set working directory
WORKDIR /app/bazarr/bin

# Copy requirements first for caching
COPY requirements.txt postgres-requirements.txt ./

# Install Python dependencies
RUN \
  pip install --break-system-packages -U --no-cache-dir --find-links https://wheel-index.linuxserver.io/alpine-3.22/ \
    -r requirements.txt \
    -r postgres-requirements.txt && \
  apk del build-dependencies

# Copy application files
COPY bazarr.py ./
COPY libs ./libs
COPY custom_libs ./custom_libs
COPY bazarr ./bazarr
COPY migrations ./migrations

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/build ./frontend/build

# Environment variables
ENV SZ_USER_AGENT="bazarr-test"
ENV BAZARR_VERSION="parallel-tasks-test"
ENV PYTHONPATH="/app/bazarr/bin/custom_libs:/app/bazarr/bin/libs:/app/bazarr/bin/bazarr:/app/bazarr/bin"

# Expose Bazarr port
EXPOSE 6767

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:6767/api/system/health || exit 1

# Volume for persistent data
VOLUME /config

# Default command
CMD ["python3", "bazarr.py", "--no-update", "--config", "/config"]
