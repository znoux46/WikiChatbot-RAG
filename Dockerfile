# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for vector database
RUN mkdir -p /app/data/chroma_db

# Expose port
EXPOSE 8000

# Health check (Railway will handle this, so we can remove or make it dynamic)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#     CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application
# Railway sets PORT environment variable, default to 8000 if not set
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
