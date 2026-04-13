# PhantomNet Agent Installer for Windows
#
# This script automates the installation and setup of the PhantomNet agent
# as a Windows service.
#
# Usage: Run this script as Administrator.

# --- Helper Functions ---
function Print-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Print-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# --- Main Script ---

Print-Info "Starting PhantomNet Agent Installation for Windows..."

# 1. Check for Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Print-Error "Please run this script as Administrator."
    exit 1
}

# 2. Set installation directory
$AgentDir = "C:\Program Files\PhantomNet Agent"
Print-Info "Creating installation directory at $AgentDir..."
if (-not (Test-Path $AgentDir)) {
    New-Item -Path $AgentDir -ItemType Directory
}
Copy-Item -Path "..\phantomnet_agent\*" -Destination $AgentDir -Recurse -Force
Print-Success "Agent files copied to $AgentDir."

# 3. Create virtual environment and install dependencies
Print-Info "Creating Python virtual environment..."
python -m venv "$AgentDir\venv"
& "$AgentDir\venv\Scripts\activate"

Print-Info "Installing Python dependencies..."
pip install -r "$AgentDir\requirements.txt"
if ($LASTEXITCODE -ne 0) {
    Print-Error "Failed to install Python dependencies."
    exit 1
}
Print-Success "Python dependencies installed."

# 4. Set up Windows service
Print-Info "Setting up Windows service..."
$ServiceName = "PhantomNetAgent"
$DisplayName = "PhantomNet Agent"
$Description = "PhantomNet Agent for telemetry collection and response."
$PythonPath = "$AgentDir\venv\Scripts\python.exe"
$ScriptPath = "$AgentDir\main.py"
$Arguments = "--config `"$AgentDir\config\agent.yml`""

# Using nssm (assumed to be available or can be downloaded)
$NssmPath = "nssm.exe" # Assuming nssm is in PATH or current directory
if (-not (Get-Command $NssmPath -ErrorAction SilentlyContinue)) {
    Print-Error "nssm.exe not found. Please download it and place it in the current directory or in your PATH."
    exit 1
}

Print-Info "Installing service with nssm..."
& $NssmPath install $ServiceName $PythonPath $ScriptPath $Arguments
& $NssmPath set $ServiceName AppDirectory $AgentDir
& $NssmPath set $ServiceName DisplayName $DisplayName
& $NssmPath set $ServiceName Description $Description
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

Print-Info "Starting PhantomNet agent service..."
& $NssmPath start $ServiceName

$Service = Get-Service -Name $ServiceName
if ($Service.Status -eq "Running") {
    Print-Success "PhantomNet agent service started successfully."
} else {
    Print-Error "Failed to start PhantomNet agent service."
    exit 1
}

exit 0
