# Dockerfile.event_stream_processor
FROM python:3.11-slim-buster

WORKDIR /app

# Install dependencies (assuming backend_api/requirements.txt is sufficient for now)
COPY backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install psutil # Event stream processor has collectors that use psutil

# Copy the necessary backend_api components
COPY backend_api ./backend_api
COPY phantomnet_agent ./phantomnet_agent # For shared schemas/modules, like collectors if they were here
COPY .env .env # For environment variables

# Command to run the Event Stream Processor
# This assumes event_stream_processor.py's __main__ block is designed to run the service
CMD ["python", "-m", "backend_api.event_stream_processor"]
