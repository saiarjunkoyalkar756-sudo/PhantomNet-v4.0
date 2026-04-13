import subprocess
import sys
import os
import time
import shutil
import argparse

# --- Configuration ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend_api")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "dashboard_frontend")
BACKEND_REQUIREMENTS = os.path.join(BACKEND_DIR, "requirements.txt")
PID_FILE = os.path.join(PROJECT_ROOT, "phantomnet.pid")

# --- Helper Functions ---
def check_prerequisites():
    """Checks if required tools are installed."""
    print("--- Checking Prerequisites ---")
    if not shutil.which("python"):
        print("Error: python is not installed or not in the PATH.")
        sys.exit(1)
    if not shutil.which("npm"):
        print("Error: npm is not installed or not in the PATH.")
        sys.exit(1)
    print("All prerequisites are met.")

def run_command(command, cwd=PROJECT_ROOT, check_error=True):
    print(f"\nRunning command: {' '.join(command)} in {cwd}")
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if check_error and process.returncode != 0:
        print(f"Error: Command failed with exit code {process.returncode}")
        print("Stdout:", process.stdout)
        print("Stderr:", process.stderr)
        sys.exit(1)
    print("Stdout:", process.stdout)
    if process.stderr:
        print("Stderr:", process.stderr)
    return process

def start_process_background(command, cwd=PROJECT_ROOT):
    print(f"\nStarting background process: {' '.join(command)} in {cwd}")
    process = subprocess.Popen(command, cwd=cwd, text=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Process started with PID: {process.pid}")
    return process

def stop_services():
    """Stops the services."""
    print("--- Stopping PhantomNet Services ---")
    if not os.path.exists(PID_FILE):
        print("PID file not found. Are the services running?")
        return

    with open(PID_FILE, "r") as f:
        pids = f.read().strip().split("\n")

    for pid_str in pids:
        try:
            pid = int(pid_str)
            # Terminate the process group
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)])
            print(f"Sent SIGTERM to process with PID {pid}")
        except (ValueError, ProcessLookupError):
            pass

    os.remove(PID_FILE)
    print("Services shut down.")

# --- Main Deployment Logic ---
def deploy_phantomnet():
    check_prerequisites()
    print("--- Starting PhantomNet Deployment ---")

    # 1. Install Python Dependencies
    print("\n--- Installing Python Dependencies for Backend ---")
    run_command([sys.executable, "-m", "pip", "install", "-r", BACKEND_REQUIREMENTS])

    # 2. Initialize Database
    print("\n--- Initializing Database ---")
    if os.path.exists(os.path.join(BACKEND_DIR, "test.db")):
        os.remove(os.path.join(BACKEND_DIR, "test.db"))
        print("Removed existing test.db to ensure a fresh start.")
    run_command([sys.executable, os.path.join(BACKEND_DIR, "database.py")])

    # 3. Install Node.js Dependencies for Frontend
    print("\n--- Installing Node.js Dependencies for Frontend ---")
    run_command(["npm", "install"], cwd=FRONTEND_DIR)

    # 4. Build Frontend
    print("\n--- Building Frontend ---")
    run_command(["npm", "run", "build"], cwd=FRONTEND_DIR)

    # 5. Start Backend API
    print("\n--- Starting Backend API (FastAPI) ---")
    backend_process = start_process_background(
        [sys.executable, "-m", "uvicorn", "backend_api.api_gateway.app:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=PROJECT_ROOT
    )
    print(f"Backend API started. PID: {backend_process.pid}")

    # 6. Start Frontend Development Server
    print("\n--- Starting Frontend Development Server ---")
    frontend_process = start_process_background(["npm", "start"], cwd=FRONTEND_DIR)
    print(f"Frontend server started. PID: {frontend_process.pid}")

    with open(PID_FILE, "w") as f:
        f.write(f"{backend_process.pid}\n")
        f.write(f"{frontend_process.pid}\n")

    print("\n--- Deployment Complete! ---")
    print(f"PhantomNet Backend API should be running on: http://0.0.0.0:8000")
    print(f"PhantomNet Frontend Dashboard should be running on: http://localhost:3000")
    print("\nTo stop the services, run: python run_all.py stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_services()
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the PhantomNet project.")
    parser.add_argument("action", nargs="?", default="start", choices=["start", "stop"], help="The action to perform.")
    args = parser.parse_args()

    if args.action == "start":
        deploy_phantomnet()
    elif args.action == "stop":
        stop_services()
