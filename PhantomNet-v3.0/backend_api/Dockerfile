# Stage 1: Build the application
FROM python:3.11-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Stage 2: Create the final image
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app /app

CMD ["uvicorn", "api_gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]