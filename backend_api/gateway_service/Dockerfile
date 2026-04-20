# Use a specific, lightweight Python version for reproducibility.
FROM python:3.11-slim as builder

# Set the working directory in the container.
WORKDIR /app

# 1. Install dependencies from the specific service requirements
# We copy from the host project root path to the container root
COPY backend_api/gateway_service/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. Copy the shared library and the service code
# This requires the Docker build context to be set to the Project Root (.)
COPY backend_api/shared ./backend_api/shared
COPY backend_api/gateway_service ./backend_api/gateway_service

# 3. Create a bridge hook to handle the package structure
# This ensures that 'from backend_api.shared import ...' works correctly
ENV PYTHONPATH="/app"

# --- Final Stage ---
FROM python:3.11-slim
RUN groupadd -g 1001 phantom && \
    useradd -u 1001 -g phantom -s /bin/sh phantom

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN chown -R phantom:phantom /app
USER phantom

# Set execution path to the service directory
WORKDIR /app/backend_api/gateway_service
EXPOSE 8000

ENV PYTHONPATH="/app"

# Command to run the Uvicorn server pointing to the main app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]