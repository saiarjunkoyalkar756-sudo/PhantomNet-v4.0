# Dockerfile.backend
FROM python:3.11-slim-buster

WORKDIR /app

# Install dependencies
COPY backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend_api and phantomnet_agent (for shared schemas/modules)
COPY backend_api ./backend_api
COPY phantomnet_agent ./phantomnet_agent
COPY .env .env # For environment variables

# Command to run the API Gateway
CMD ["uvicorn", "backend_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
