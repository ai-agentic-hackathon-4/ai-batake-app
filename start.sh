#!/bin/bash

# Start the Python Backend in the background
# We run it on port 8081 as configured in our design
echo "Starting Backend on port 8081..."
uvicorn backend.main:app --host 127.0.0.1 --port 8081 &
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
echo "Starting Frontend on port ${PORT:-8080}..."
cd frontend

# Use npx next start to ensure we pass the correct port and host
# We use -- to pass arguments to the underlying next command if using npm start,
# but calling npx next start directly is clearer.
# Next.js 13.4.1+ should pick up PORT, but being explicit is safer.
npx next start -p ${PORT:-8080} -H 0.0.0.0
