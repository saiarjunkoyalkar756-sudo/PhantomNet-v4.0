# Stop-PhantomNet.ps1
# Script to stop PhantomNet Agent and Backend services on Windows

$SERVICE_AGENT_NAME = "PhantomNetAgent"
$SERVICE_BACKEND_NAME = "PhantomNetBackend"

function Log-Info {
    Param([string]$Message)
    Write-Host "INFO: $Message"
}

function Log-Error {
    Param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

Log-Info "Attempting to stop PhantomNet Agent service..."
try {
    Stop-Service $SERVICE_AGENT_NAME -ErrorAction Stop
    Log-Info "PhantomNet Agent service stopped successfully."
} catch {
    Log-Error "Failed to stop PhantomNet Agent service: $($_.Exception.Message)"
}

Log-Info "Attempting to stop PhantomNet Backend service..."
try {
    Stop-Service $SERVICE_BACKEND_NAME -ErrorAction Stop
    Log-Info "PhantomNet Backend service stopped successfully."
} catch {
    Log-Error "Failed to stop PhantomNet Backend service: $($_.Exception.Message)"
}

Log-Info "PhantomNet services shutdown sequence complete."
