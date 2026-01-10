#!/bin/bash

# Start the Python Backend in the background
# We run it on port 8081 as configured in our design
echo "Starting Backend on port 8081..."
uvicorn backend.main:app --host 127.0.0.1 --port 8081 &

# Start the Node Frontend
# It will listen on the PORT environment variable (default 8080 provided by Cloud Run)
echo "Starting Frontend..."
cd frontend
node server.js
