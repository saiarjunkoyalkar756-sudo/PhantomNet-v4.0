FROM python:3.9-slim-buster

# YARA requires libyara-dev
# For now, we assume yara-python is installed if needed, this Dockerfile does not build it
# RUN apt-get update && apt-get install -y libyara-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]