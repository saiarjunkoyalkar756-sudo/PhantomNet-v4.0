### Deployment Notes

These notes outline the key considerations for deploying the updated PhantomNet system with live log streaming.

**1. Backend (API Gateway) Deployment:**

*   **Dependencies:** Ensure Python dependencies, especially `FastAPI`, `uvicorn`, `watchfiles`, `python-json-logger` (if not already present), and `aiohttp` are installed (`pip install -r requirements.txt`).
*   **Logging Configuration:** The backend is configured to use `RotatingFileHandler` for `backend_api/file.log`.
    *   `MAX_BYTES`: 10 MB per log file.
    *   `BACKUP_COUNT`: 5 backup files will be kept.
    *   Adjust these values in `backend_api/main.py` if different retention policies are required.
*   **WebSocket Endpoints:**
    *   `/ws/logs`: For dashboard clients to receive aggregated log streams.
    *   `/ws/logs/agent`: For PhantomNet agents to send their logs to the backend.
*   **Firewall Rules:** Ensure that inbound connections to the backend's port (default 8000) are allowed for both HTTP/HTTPS (for the main API) and WebSocket traffic from dashboard clients and PhantomNet agents.
*   **Scaling:** For high-volume log environments, consider deploying multiple instances of the backend API behind a load balancer. The `log_buffer` in `log_streamer.py` is in-memory; for distributed log processing, a message queue (like Kafka or Redis Pub/Sub) would be required to aggregate logs before sending to individual dashboard connections. This MVP design assumes a single backend instance or a sticky-session load balancer for dashboard WebSocket connections.
*   **Log File Paths:** The `LOG_FILE_PATHS` variable in `backend_api/main.py` specifies the local log files to monitor. Ensure these paths are correct for the deployment environment.

**2. PhantomNet Agent Deployment:**

*   **Dependencies:** Ensure Python dependencies like `aiohttp`, `watchfiles`, `python-json-logger`, etc., are installed in the agent's environment.
*   **Logging Configuration:** The agent's logging is configured via `phantomnet_agent/core/logging_config.py` to use `RotatingFileHandler` for `phantomnet_agent/agent_output.log`.
    *   `MAX_BYTES`: 10 MB per log file.
    *   `BACKUP_COUNT`: 5 backup files will be kept.
    *   Adjust these values in `phantomnet_agent/core/logging_config.py` as needed.
*   **Backend URL:** The `LogForwarder` in `phantomnet_agent/main.py` is configured to connect to `ws://{config.agent.manager_host}:8000/ws/logs/agent`. Ensure `config.agent.manager_host` correctly points to the backend API Gateway's address. If the backend uses HTTPS, change `ws://` to `wss://`.
*   **Network Access:** Ensure the agent can establish outbound WebSocket connections to the backend API Gateway.
*   **Resource Usage:** Monitor the agent's CPU and memory usage, especially if log volume is very high, as `watchfiles` and the `LogForwarder` consume resources.

**3. Dashboard Frontend Deployment:**

*   **Dependencies:** Ensure Node.js and npm/yarn are available for building the React application. Install all frontend dependencies (`npm install`).
*   **Build Process:** Build the React application for production (`npm run build`). Serve the static files from the `build` or `dist` directory using a web server (e.g., Nginx, Apache, or a static file host).
*   **WebSocket URL:** The `LiveLogTerminal.jsx` component connects to `ws://localhost:8000/ws/logs`.
    *   **Crucial:** This `localhost` address *must* be changed to the actual domain name or IP address of your deployed backend API Gateway. For example, `ws://your-backend-domain.com/ws/logs` or `wss://your-backend-domain.com/ws/logs` if HTTPS is used.
    *   This change should be made during the build process, possibly using environment variables (`.env` files) that are injected by the build system.
*   **Firewall Rules:** Ensure inbound HTTP/HTTPS traffic to the web server hosting the frontend is allowed.
*   **Browser Compatibility:** Test the log viewer in target browsers to ensure WebSocket and UI rendering compatibility.

**General Considerations:**

*   **Security (mTLS/Authentication):** The current implementation uses mock IAM. In a production environment, implement robust mTLS for inter-service communication (between agent and backend) and proper authentication/authorization for dashboard users. This would involve configuring certificates and integrating with a real IAM service.
*   **Environment Variables:** Use environment variables for sensitive information (e.g., API keys, database credentials) and configurable parameters (e.g., backend URLs, log retention settings) rather than hardcoding them.
*   **Monitoring & Alerting:** Implement monitoring for the health and performance of the backend, agents, and frontend components, with alerts for disconnections, high error rates, or excessive resource consumption.
*   **Containerization:** It is highly recommended to containerize (e.g., Docker) each microservice (backend, agent, frontend) for consistent deployment across different environments. Refer to the existing `Dockerfile`s as a starting point.
*   **Orchestration:** For multi-service deployments, use an orchestration platform like Docker Compose (for local dev/small deployments) or Kubernetes (for production-grade, scalable deployments).

This completes the request.