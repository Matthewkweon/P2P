FROM python:3.12.4-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY setup.py .
COPY pyproject.toml .
COPY README.md .
COPY launcher.py .
COPY src/ ./src/
COPY static/ ./static/

# Install the package in development mode
RUN pip install -e .

# Create logs directory
RUN mkdir -p logs

# Environment variables (can be overridden during runtime)
ENV MONGO_URL=mongodb://mongo:27017
ENV OPENAI_API_KEY=your_openai_api_key_here

# Expose ports for each service
# Message API port
EXPOSE 8000
# Chat server port
EXPOSE 5000
# Web interface port
EXPOSE 8080

# Default command to run the launcher script
CMD ["python", "launcher.py"]