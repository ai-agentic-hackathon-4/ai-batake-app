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
# Run the custom Express server (server.js) which handles:
# 1. Serving static files at /dashboard
# 2. Proxying /api requests to the backend
# 3. Serving a root landing page
cd frontend
node server.js

