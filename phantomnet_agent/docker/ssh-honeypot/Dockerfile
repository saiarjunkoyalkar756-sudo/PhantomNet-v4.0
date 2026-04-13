# docker/ssh-honeypot/Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
# Copy requirements.txt from the project root
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary application code
COPY honeypots ./honeypots
COPY backend_api/honeypot_service ./backend_api/honeypot_service

# Copy the wrapper script
COPY docker/ssh-honeypot/run_honeypot.py .

# Expose the default SSH honeypot port
EXPOSE 2222

# Define environment variables for the honeypot
ENV HONEYPOT_ID="docker-ssh-honeypot"
ENV HONEYPOT_PORT="2222"
ENV HONEYPOT_HOST="0.0.0.0"

# Run the honeypot script when the container launches
CMD ["python", "run_honeypot.py"]
