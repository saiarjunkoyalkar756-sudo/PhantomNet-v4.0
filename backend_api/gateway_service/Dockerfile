# Use a specific, lightweight Python version for reproducibility.
FROM python:3.11-slim as builder

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching.
COPY requirements.txt .

# Install dependencies.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the shared code library into the application directory.
# This assumes the build context is the 'gateway_service' directory.
COPY ../shared ./shared

# Copy the rest of the gateway service application code.
COPY . .

# --- Final Stage ---

# Use the same base image for the final, lean image.
FROM python:3.11-slim

# Set the working directory.
WORKDIR /app

# Copy the installed application (including dependencies and shared code)
# from the builder stage.
COPY --from=builder /app /app

# Expose the port the app runs on.
EXPOSE 8000

# Command to run the Uvicorn server.
# --host 0.0.0.0 makes the server accessible from outside the container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]