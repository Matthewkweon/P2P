FROM python:3.12-slim

WORKDIR /app

# Install necessary system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create directory for logs
RUN mkdir -p logs

# Expose necessary ports
EXPOSE 5000 8000 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "launcher.py"]