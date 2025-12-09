# Use a slim Python image for smaller size
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirement files and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code into the container
COPY . /app

# Expose the port the application runs on
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "scripts.api_server:app", "--host", "0.0.0.0", "--port", "8000"]