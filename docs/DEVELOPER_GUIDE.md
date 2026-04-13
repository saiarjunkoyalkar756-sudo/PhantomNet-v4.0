# PhantomNet Developer Guide

This guide provides instructions on how to set up the development environment, run the project, and contribute to it.

## Development Environment Setup

### Prerequisites

*   [Python 3.11+](https://www.python.org/downloads/)
*   [Node.js 18+](https://nodejs.org/en/download/)
*   [Docker](https://www.docker.com/products/docker-desktop/) (optional, but recommended)

### Backend Setup

1.  **Create a virtual environment:**

    ```bash
    cd backend_api
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### Frontend Setup

1.  **Install the dependencies:**

    ```bash
    cd dashboard_frontend
    npm install
    ```

## Running the Project

### With Docker Compose (Recommended)

1.  **Copy the environment file:**

    ```bash
    cp .env.example .env
    ```

2.  **Start the services:**

    ```bash
    docker-compose up --build
    ```

The services will be available at the following URLs:

*   **Frontend:** http://localhost:3000
*   **Backend:** http://localhost:8000

### Manually

1.  **Start the backend:**

    ```bash
    cd backend_api
    uvicorn api_gateway.app:app --host 0.0.0.0 --port 8000
    ```

2.  **Start the frontend:**

    ```bash
    cd dashboard_frontend
    npm start
    ```

## Contributing

We welcome contributions to PhantomNet! Please follow these steps to contribute:

1.  **Fork the repository.**
2.  **Create a new branch for your feature or bug fix.**
3.  **Make your changes.**
4.  **Write tests for your changes.**
5.  **Run the tests:**

    *   **Backend:**

        ```bash
        cd backend_api
        pytest
        ```

    *   **Frontend:**

        ```bash
        cd dashboard_frontend
        npm test
        ```

6.  **Submit a pull request.**
