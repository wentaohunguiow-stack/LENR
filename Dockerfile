FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ghostscript \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt requirements-api.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY lenr_collection/ ./lenr_collection/
COPY api.py ./

# Create directories
RUN mkdir -p pdfs logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
