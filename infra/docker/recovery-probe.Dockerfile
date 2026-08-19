FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir kafka-python==2.0.2 psycopg2-binary==2.9.9

COPY scripts/run_docker_recovery_validation.py /app/run_docker_recovery_validation.py
COPY backend_api/audit_log_collector/integrity.py /app/phantomnet_audit_integrity.py

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "/app/run_docker_recovery_validation.py"]
