# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY ../../backend_api/alert_storage/requirements.txt .

# Install any needed packages specified in requirements.txt
# We need build-essential and libpq-dev for psycopg2
RUN apt-get update && apt-get install -y build-essential libpq-dev && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY ../../backend_api/alert_storage/ .

# Run the storage script when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
