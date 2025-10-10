#!/bin/bash

echo "Testing Bazarr Development Setup..."
echo "=================================="

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

echo "✅ Data directory is ready"

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
echo "   docker compose up --build"
echo ""
echo "Once started:"
echo "   - Frontend will be available at: http://localhost:5173"
echo "   - Backend API will be available at: http://localhost:6767"
