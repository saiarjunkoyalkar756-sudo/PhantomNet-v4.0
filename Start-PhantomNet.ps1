# Start-PhantomNet.ps1
# Script to start PhantomNet Agent and Backend services on Windows

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

Log-Info "Attempting to start PhantomNet Backend service..."
try {
    Start-Service $SERVICE_BACKEND_NAME -ErrorAction Stop
    Log-Info "PhantomNet Backend service started successfully."
} catch {
    Log-Error "Failed to start PhantomNet Backend service: $($_.Exception.Message)"
}

Log-Info "Attempting to start PhantomNet Agent service..."
try {
    Start-Service $SERVICE_AGENT_NAME -ErrorAction Stop
    Log-Info "PhantomNet Agent service started successfully."
} catch {
    Log-Error "Failed to start PhantomNet Agent service: $($_.Exception.Message)"
}

Log-Info "PhantomNet services startup sequence complete."
