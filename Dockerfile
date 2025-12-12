FROM python:3.10-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "scripts.api_server:app", "--host", "0.0.0.0", "--port", "8000"]