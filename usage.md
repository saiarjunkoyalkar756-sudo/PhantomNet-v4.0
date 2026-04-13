# PhantomNet Usage Guide

## 1. Overview

PhantomNet is an AI-driven autonomous cybersecurity framework designed to provide advanced threat detection, analysis, and response capabilities. It leverages a distributed microservice architecture, a React-based frontend for intuitive interaction, a blockchain audit layer for immutable logging, and a neural threat analysis engine for intelligent decision-making.

This guide will walk you through setting up, running, and interacting with the PhantomNet system.

## 2. Getting Started

To get PhantomNet up and running, you have two primary options: using Docker Compose (recommended for ease of setup) or running each component manually.

### Option A: Using Docker Compose (Recommended)

This method simplifies the setup process by orchestrating all services (backend, analyzer, frontend, database, Redis) with a single command.

1.  **Ensure Docker is Installed:** Make sure you have Docker and Docker Compose installed on your system.
2.  **Navigate to the Project Root:**
    ```bash
    cd /path/to/PhantomNet-v3.0
    ```
3.  **Build and Run Services:**
    ```bash
    docker-compose up --build
    ```
    This command will build the necessary Docker images and start all services. It might take some time on the first run.

### Option B: Running Manually

If you prefer to run each component separately, follow the detailed instructions below. This requires setting up Python virtual environments and Node.js dependencies for each service.

#### 2.1. Backend (`backend_api`)

**Prerequisites:** Python 3.10+, `pip`

1.  **Navigate to the backend directory:**
    ```bash
    cd backend_api
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows: .\venv\Scripts\activate
    # macOS/Linux: source venv/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set environment variables:** Create a `.env` file in `backend_api` with:
    ```
    DATABASE_URL="postgresql://user:password@localhost/dbname"
    SECRET_KEY="your_super_secret_key"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ANALYZER_SERVICE_URL="http://localhost:8001" # Or the port your analyzer runs on
    ```
    *(Ensure a PostgreSQL database is running and accessible.)*
5.  **Run database migrations (if applicable):**
    ```bash
    # Example: alembic upgrade head
    ```
6.  **Run the FastAPI application:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

#### 2.2. Analyzer (`backend_api/analyzer`)

**Prerequisites:** Python 3.10+, `pip`

1.  **Navigate to the analyzer directory:**
    ```bash
    cd backend_api/analyzer
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv_analyzer
    # Windows: .\venv_analyzer\Scripts\activate
    # macOS/Linux: source venv_analyzer/bin/activate
    ```
3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the FastAPI application:**
    ```bash
    uvicorn app:app --host 0.0.0.0 --port 8001 --reload # Use a different port than backend_api
    ```

#### 2.3. Frontend (`dashboard_frontend`)

**Prerequisites:** Node.js (LTS), `yarn` (or `npm`)

1.  **Navigate to the frontend directory:**
    ```bash
    cd dashboard_frontend
    ```
2.  **Install Node.js dependencies:**
    ```bash
    yarn install
    ```
3.  **Set environment variables:** Create a `.env` file in `dashboard_frontend` with:
    ```
    VITE_API_BASE_URL=http://localhost:8000 # Or the port your backend runs on
    ```
4.  **Run the Vite development server:**
    ```bash
    yarn dev
    ```
    Access the application in your browser at `http://localhost:3000`.

## 3. Key Features & Usage

Once the PhantomNet system is running, you can interact with its various features through the web dashboard.

### 3.1. Authentication

*   **Login Page (`/login`):** Enter your username and password. If 2FA is enabled, you will be prompted for a TOTP code or a recovery code.
*   **2FA Setup (`/2fa-setup`):** Manage your two-factor authentication settings.

### 3.2. Dashboard Overview (`/dashboard`)

The main dashboard provides a summary of the system's status, including:

*   **Security Insights Card:** Displays high-level security metrics.
*   **Health Status Widget:** Shows the operational health of various PhantomNet components.
*   **Security Alerts:** Lists recent security notifications.
*   **AI Assistant (Chatbot):** A conversational AI agent to help you understand and interact with the system using natural language.

### 3.3. AI Assistant (Chatbot)

Located on the main dashboard, the AI Assistant allows you to:

*   **Ask Questions:** Type your queries about system status, threats, or general cybersecurity topics.
*   **Receive Explanations:** Get clear, concise answers and explanations from the AI.
*   **Conversation History:** The chatbot maintains a conversation history to provide context-aware responses.

### 3.4. AI Threat Brain (`/ai-threat-brain`)

This module allows you to simulate attacks and analyze potential threats with AI-driven explanations.

*   **Simulate Attack:** Enter threat data (e.g., suspicious log entries, potential attack patterns) into the text area and click "Simulate."
*   **View Analysis:** The AI will provide an "Attack Type," "Confidence Score," and a detailed "Explanation" of its decision, highlighting why it classified the threat as such.
*   **Threat Scoring & Evolution:** Visualizations (Bar Chart, Line Chart) track the confidence and evolution of simulated threats over time.

### 3.5. Admin Dashboard (`/admin`)

Accessible only to users with the 'admin' role, this section provides comprehensive management tools:

*   **User Management:** View, update roles (User, Analyst, Admin), disable, and enable user accounts.
*   **Audit Log (`/admin/audit`):** Review detailed records of system activities and administrative actions.
*   **Network Map (`/network-map`):** Visualize the network of PhantomNet agents.
*   **Attack Map (`/attack-map`):** See real-time attack visualizations.
*   **Federation Settings (`/federation-settings`):** Manage agent federation, Certificate Authorities (CA), and bootstrap tokens.

### 3.6. Blockchain Viewer (`/blockchain`)

View the immutable audit trail recorded on the PhantomChain. This provides transparency and integrity for critical system events.

## 4. Troubleshooting

*   **"Could not connect to Analyzer service" / "API request failed":**
    *   Ensure all backend services (backend_api, analyzer, db, redis) are running.
    *   Check environment variables (`ANALYZER_SERVICE_URL`, `VITE_API_BASE_URL`) for correct hostnames and ports.
    *   Verify no port conflicts if running manually.
*   **Frontend not loading / blank page:**
    *   Check the browser's developer console for errors.
    *   Ensure the frontend development server (`yarn dev`) is running.
    *   Verify `VITE_API_BASE_URL` in `dashboard_frontend/.env` points to the correct backend address.
*   **AI models not loading (Analyzer service):**
    *   Ensure the `transformers` and `datasets` libraries are correctly installed in the analyzer's virtual environment.
    *   Check the analyzer service logs for model download or loading errors. This might require a stable internet connection on first run.
*   **Access Denied on Admin pages:**
    *   Ensure you are logged in with a user account that has the 'admin' role.

For further assistance, refer to the `DEVELOPER_GUIDE.md` or `API_DOCUMENTATION.md` files.
