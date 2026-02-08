#!/bin/bash

# # Cleanup existing backend and frontend processes if any
# echo "Cleaning up ports 8081 and 3000..."
# fuser -k 8081/tcp || true
# fuser -k 3000/tcp || true

# Start the Python Backend in the background
# We run it on port 8081 as configured in our design
# echo "Cleaning up ports 8081 and 3000..."
# fuser -k 8081/tcp || true
# fuser -k 3000/tcp || true
echo "Starting Backend on port 8081..."
# ./venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8081 &
uvicorn backend.main:app --host 0.0.0.0 --port 8081 &

BACKEND_PID=$!

# Wait for backend to initialize (optional but helpful for logs)
sleep 5

# Check if backend is still running
if ! kill -0 $BACKEND_PID > /dev/null 2>&1; then
    echo "Backend failed to start!"
    exit 1
fi

# Start the Node Frontend
# It will listen on the PORT environment variable (default 8080 provided by Cloud Run)
echo "Starting Frontend on port ${PORT:-3000}..."
cd frontend
# Start Next.js in production mode
npx next start -p ${PORT:-3000} -H 0.0.0.0
