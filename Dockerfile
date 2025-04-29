FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create entrypoint script
RUN echo '#!/bin/sh\n\
if [ "$SERVICE" = "api" ]; then\n\
  exec python message_api.py --host 0.0.0.0 --port 8000\n\
elif [ "$SERVICE" = "server" ]; then\n\
  exec python async_server.py --host 0.0.0.0 --port 5000 --api-base http://api:8000\n\
elif [ "$SERVICE" = "web" ]; then\n\
  exec python websocket_adapter.py --host 0.0.0.0 --port 8080 --server-host server --server-port 5000 --api-base http://api:8000\n\
elif [ "$SERVICE" = "thermometer" ]; then\n\
  exec python thermometer.py --host server --port 5000 --api-base http://api:8000 --redis-host redis\n\
elif [ "$SERVICE" = "openai" ]; then\n\
  if [ -z "$OPENAI_API_KEY" ]; then\n\
    echo "ERROR: OPENAI_API_KEY environment variable is not set"\n\
    exit 1\n\
  fi\n\
  exec python openai.py --host server --port 5000 --api-base http://api:8000\n\
elif [ "$SERVICE" = "all" ]; then\n\
  # Start all services using launcher script\n\
  exec python launcher.py --redis-host redis\n\
else\n\
  echo "Unknown service: $SERVICE"\n\
  echo "Available services: api, server, web, thermometer, openai, all"\n\
  exit 1\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]