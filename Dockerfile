# Use a Python base image that is relatively small
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files and install Python dependencies
COPY backend ./backend
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy frontend files and install Node.js dependencies
COPY frontend ./frontend
WORKDIR /app/frontend
RUN npm install
WORKDIR /app

# Copy the start script
COPY start.sh .
RUN chmod +x start.sh

# Expose the port Cloud Run expects
ENV PORT=8080
# Set the Agent Engine endpoint here.
# Replace with your actual resource name: projects/PROJECT_ID/locations/LOCATION/reasoningEngines/ID
ENV AGENT_ENDPOINT="projects/ai-agentic-hackathon-4/locations/us-central1/reasoningEngines/3602682889315024896"
EXPOSE 8080

CMD ["./start.sh"]
