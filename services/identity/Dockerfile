FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared utilities
COPY ./shared /app/shared

# Copy requirements and install dependencies
COPY ./services/identity/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./services/identity .


# Run server (tables will be created automatically on startup)
CMD uvicorn main:app --host 0.0.0.0 --port 8000
