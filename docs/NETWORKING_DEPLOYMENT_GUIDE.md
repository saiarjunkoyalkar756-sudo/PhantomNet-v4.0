# Networking Security Layer Deployment Guide

This document provides instructions for deploying and running the PhantomNet Networking Security Layer.

## Prerequisites

- Python 3.9+
- Node.js 16+
- Docker
- Docker Compose

## Environment Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/phantomnet.git
    cd phantomnet
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Node.js dependencies:**
    ```bash
    cd dashboard_frontend
    npm install
    cd ..
    ```

4.  **Set up the environment variables:**
    Create a `.env` file in the root directory and add the following:
    ```
    JWT_SECRET_KEY=your-secret-key
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092
    ```

## Running the Backend Services

1.  **Start the infrastructure:**
    This will start Kafka, Zookeeper, and Redpanda.
    ```bash
    docker-compose up -d
    ```

2.  **Run the database migrations:**
    ```bash
    alembic upgrade head
    ```

3.  **Start the backend services:**
    ```bash
    # Start the gateway service
    uvicorn backend_api.gateway_service.main:app --host 0.0.0.0 --port 8000 --reload

    # Start the AI Behavioral Engine
    python backend_api.ai_behavioral_engine.main.py

    # Start the SOAR Engine
    python backend_api.soar_engine.main.py
    ```

## Running the Frontend

1.  **Start the development server:**
    ```bash
    cd dashboard_frontend
    npm run dev
    ```

## Running the Agent

1.  **Configure the agent:**
    Update the `config.json` file in the `phantomnet_agent` directory with the correct manager URL.

2.  **Run the agent:**
    ```bash
    python phantomnet_agent/main.py
    ```
