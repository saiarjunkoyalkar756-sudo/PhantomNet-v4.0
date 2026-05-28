# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the root requirements file
COPY requirements.txt .

# Install all needed packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend_api to handle shared/core dependencies
COPY backend_api ./backend_api

# Set the PYTHONPATH to include the app directory
ENV PYTHONPATH="/app"

# Set execution path to the service directory
WORKDIR /app/backend_api/telemetry_ingestor

# Run uvicorn when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
