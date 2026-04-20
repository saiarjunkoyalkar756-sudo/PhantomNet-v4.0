# Use a specific, lightweight Python version for reproducibility.
FROM python:3.11-slim as builder

WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching.
COPY backend_api/ai_agent_orchestrator/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the shared code library and the service code
COPY backend_api/shared ./backend_api/shared
COPY backend_api/ai_agent_orchestrator ./backend_api/ai_agent_orchestrator

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
WORKDIR /app/backend_api/ai_agent_orchestrator
EXPOSE 8000

ENV PYTHONPATH="/app"

# Command to run the Uvicorn server.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
