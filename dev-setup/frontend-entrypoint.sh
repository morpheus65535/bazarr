#!/bin/sh

echo "Waiting for backend to be ready..."

# Wait for backend to be reachable
until nc -z bazarr-backend 6767 2>/dev/null; do
    echo "Backend not ready yet, waiting..."
    sleep 5
done

echo "Backend is ready!"

# In development mode, we don't need to wait for API key since authentication might be disabled
echo "Starting frontend in development mode..."

# Start the frontend with --no-open to prevent browser auto-open attempts in container
exec npm run start -- --host --no-open
