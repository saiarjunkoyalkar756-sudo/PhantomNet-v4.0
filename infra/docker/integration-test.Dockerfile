FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt phantomnet_agent/requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt -r phantomnet_agent/requirements.txt

COPY . .

ENV PYTHONPATH=/app:/app/phantomnet_agent

CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_live_integration_topology.py"]
