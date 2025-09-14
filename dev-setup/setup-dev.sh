#!/bin/bash

echo "Testing Bazarr Development Setup..."
echo "=================================="

# Parse command line arguments
SETUP_AUTOPULSE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --autopulse)
            SETUP_AUTOPULSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--autopulse]"
            echo ""
            echo "Options:"
            echo "  --autopulse    Also setup Autopulse for Plex integration testing"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                # Setup Bazarr only"
            echo "  $0 --autopulse   # Setup Bazarr + Autopulse"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Check if data directory exists
if [ ! -d "./data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data/config data/cache data/log data/db
else
    echo "📁 Data directory exists, ensuring subdirectories..."
    mkdir -p data/config data/cache data/log data/db
fi

# Create Autopulse data directory (conditional)
if [ "$SETUP_AUTOPULSE" = true ]; then
    if [ ! -d "./autopulse" ]; then
        echo "📁 Creating Autopulse directories..."
        mkdir -p autopulse/data
    else
        echo "📁 Autopulse directory exists, ensuring subdirectories..."
        mkdir -p autopulse/data
    fi
    echo "✅ Data directories are ready (including Autopulse)"
else
    echo "✅ Bazarr data directory is ready"
fi

# Create a minimal config for development if it doesn't exist
if [ ! -f "./data/config/config.yaml" ]; then
    echo "📝 Creating minimal config.yaml for development..."
    # The password needs to be stored as MD5 hash
    # MD5 hash of "admin" is: 21232f297a57a5a743894a0e4a801fc3
    cat > data/config/config.yaml << 'EOF'
auth:
  type: form
  apikey: 'bazarr'
  username: 'admin'
  password: '21232f297a57a5a743894a0e4a801fc3'

general:
  port: 6767
  base_url: ''
EOF
    echo "✅ Config file created with default credentials (admin/admin)"
else
    echo "✅ Config file already exists"
fi

# Create Autopulse config if it doesn't exist (conditional)
if [ "$SETUP_AUTOPULSE" = true ]; then
    if [ ! -f "./autopulse/config.yaml" ]; then
        echo "📝 Creating Autopulse config.yaml..."
        cp autopulse/config.yaml ./autopulse/config.yaml 2>/dev/null || cat > autopulse/config.yaml << 'EOF'
app:
  hostname: 0.0.0.0
  port: 2875
  database_url: sqlite://data/autopulse.db

logging:
  level: trace
EOF
        echo "✅ Autopulse config file created"
    else
        echo "✅ Autopulse config file already exists"
    fi

    # Create Autopulse Dockerfile if it doesn't exist
    if [ ! -f "./autopulse/Dockerfile" ]; then
        echo "📝 Creating Autopulse Dockerfile..."
        cat > autopulse/Dockerfile << 'EOF'
# Dockerfile to build Autopulse from any branch/PR using Debian base
# This avoids the proc-macro issues with musl target

FROM rust:slim-bookworm AS builder

# Build arguments for flexibility
ARG AUTOPULSE_REPO=https://github.com/dan-online/autopulse.git
ARG AUTOPULSE_BRANCH=main
ARG AUTOPULSE_PR=

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    libsqlite3-dev \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone the Autopulse repository
WORKDIR /src
RUN git clone ${AUTOPULSE_REPO} .

# Checkout specified branch or PR
RUN if [ -n "${AUTOPULSE_PR}" ]; then \
        echo "Building from PR #${AUTOPULSE_PR}" && \
        git fetch origin pull/${AUTOPULSE_PR}/head:pr-${AUTOPULSE_PR} && \
        git checkout pr-${AUTOPULSE_PR}; \
    else \
        echo "Building from branch ${AUTOPULSE_BRANCH}" && \
        git checkout ${AUTOPULSE_BRANCH}; \
    fi

# Update to latest stable Rust and build with both SQLite and Postgres support
RUN rustup update stable && \
    rustup default stable && \
    cargo build --release --no-default-features --features sqlite,postgres

# Runtime stage using Debian slim
FROM debian:bookworm-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    libsqlite3-0 \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN addgroup --gid 1000 app && \
    adduser --disabled-password --shell /bin/sh --uid 1000 --gid 1000 app

WORKDIR /app

# Create data directory and set permissions
RUN mkdir -p /app/data && \
    chown -R app:app /app

# Copy the compiled binary from builder stage
COPY --from=builder /src/target/release/autopulse /usr/local/bin/autopulse

# Switch to app user
USER app

# Expose port
EXPOSE 2875

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:2875/stats || exit 1

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/autopulse"]
EOF
        echo "✅ Autopulse Dockerfile created"
    else
        echo "✅ Autopulse Dockerfile already exists"
    fi
fi

# Check if both services are defined
if docker compose config --services | grep -q "bazarr-backend" && docker compose config --services | grep -q "bazarr-frontend"; then
    echo "✅ Both services (backend and frontend) are properly configured"
else
    echo "❌ Services are not properly configured in docker-compose.yml"
    exit 1
fi

# Validate the compose file
if docker compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml is valid"
else
    echo "❌ docker-compose.yml has errors"
    docker compose config
    exit 1
fi

echo ""
echo "🎉 Everything looks good! You can now run:"
if [ "$SETUP_AUTOPULSE" = true ]; then
    echo "   docker compose --profile autopulse up --build  # Start with Autopulse (configured)"
    echo "   docker compose up --build                      # Start Bazarr only"
else
    echo "   docker compose up --build                      # Start Bazarr only"
    echo "   docker compose --profile autopulse up --build  # Start with Autopulse (run './setup-dev.sh --autopulse' first)"
fi
echo ""
echo "Once started:"
echo "   - Frontend will be available at: http://localhost:5173"
echo "   - Backend API will be available at: http://localhost:6767"
if [ "$SETUP_AUTOPULSE" = true ]; then
    echo "   - Autopulse will be available at: http://localhost:2875"
fi
echo ""
echo "Default credentials:"
echo "   - Bazarr: admin/admin"
if [ "$SETUP_AUTOPULSE" = true ]; then
    echo "   - Autopulse: admin/password"
fi
