# Dockerfile.policy_engine
FROM python:3.11-slim-buster

WORKDIR /app

# Install dependencies (assuming backend_api/requirements.txt is sufficient for now)
COPY backend_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary backend_api components
COPY backend_api ./backend_api
COPY .env .env # For environment variables

# Command to run the Policy Engine API
CMD ["uvicorn", "backend_api.policy_api:router", "--host", "0.0.0.0", "--port", "8000"]
