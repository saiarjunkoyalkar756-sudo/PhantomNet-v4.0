# backend_api/honeypot_service/Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
# Copy only the requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .
# Copy the honeypots directory which is outside the current service directory
COPY ../../honeypots /app/honeypots
COPY ../../core /app/core


# Make port 8100 available to the world outside this container
EXPOSE 8100

# Run the uvicorn server when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]
