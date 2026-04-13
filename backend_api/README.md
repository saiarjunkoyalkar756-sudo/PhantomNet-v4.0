# Cybersecurity Operations Backend Platform

This project is a comprehensive, microservices-based backend platform designed for advanced cybersecurity operations. It integrates various security functions into a cohesive, scalable, and event-driven system.

This repository has been refactored to meet production-grade standards, following the principles of a 12-factor application.

## Architecture

The platform is built on a microservices architecture, orchestrated with Docker Compose.

- **API Gateway (`gateway_service`):** A central FastAPI application that acts as the primary entry point for all external traffic. It routes requests to the appropriate downstream microservices.
- **Shared Code (`shared`):** A common library containing shared database models, settings management, and utility functions. This code is packaged with services at build time.
- **Microservices:** Each business capability (e.g., `analyzer`, `asset_inventory`) is isolated in its own service directory. Each service is a standalone, containerized application with its own dependencies.
- **Message Bus (Implicit):** Services are designed to be loosely coupled. While not fully implemented in this refactor, the structure supports adding a message bus like Kafka or RabbitMQ for asynchronous communication.
- **Infrastructure:** Core services like PostgreSQL and Redis are managed by Docker Compose, providing reliable persistence and caching layers.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

1.  **Environment Configuration:**

    The system is configured via environment variables. The `docker-compose.yml` file sets the necessary variables for development. For production, you would use a `.env` file or manage secrets with an orchestration tool.

2.  **Build and Run the Services:**

    From the root of the project, run the following command:

    ```bash
    docker-compose up --build
    ```

    - `--build` forces Docker to rebuild the service images, which is necessary after making code changes.
    - The first time you run this, it will download the base images and build all the services, which may take a few minutes.

3.  **Accessing the API:**

    Once the services are running, the API Gateway will be accessible at [http://localhost:8000](http://localhost:8000). You can access the auto-generated API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

## Services Overview

| Service           | Port | Description                                                              |
| ----------------- | ---- | ------------------------------------------------------------------------ |
| `gateway`         | 8000 | The main API gateway. All external requests should go through here.      |
| `postgres`        | 5432 | The primary relational database for operational and policy data.         |
| `redis`           | 6379 | In-memory cache and message broker.                                      |
| `analyzer`        | -    | Example microservice for performing analysis (runs as a background worker). |
| `asset_inventory` | -    | Example microservice for managing asset data.                            |

## Development

### Adding a New Service

1.  **Create a Directory:** Create a new directory for your service (e.g., `my_new_service`).
2.  **Add Your Code:** Write your application logic (e.g., `app.py`).
3.  **Add a `Dockerfile`:** Create a `Dockerfile` for your service. You can use the `gateway_service/Dockerfile` as a template. If you need code from the `shared` directory, make sure to copy it in.
4.  **Add to `docker-compose.yml`:** Add a new service definition to the `docker-compose.yml` file, following the pattern of the other services.
5.  **Rebuild:** Run `docker-compose up --build` to launch your new service alongside the others.
