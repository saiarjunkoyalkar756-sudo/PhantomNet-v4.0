# Dockerfile.orchestrator
FROM python:3.11-slim-buster

WORKDIR /app

# Install dependencies (assuming backend_api/requirements.txt is sufficient for now)
COPY backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary backend_api components
COPY backend_api ./backend_api
COPY phantomnet_agent ./phantomnet_agent # For agent-related imports in orchestrator

# Command to run the Orchestrator (which hosts the /commands/dispatch endpoint)
# We can make this a simple FastAPI app running just the orchestrator_api router if needed
CMD ["uvicorn", "backend_api.orchestrator_api:router", "--host", "0.0.0.0", "--port", "8000"]
