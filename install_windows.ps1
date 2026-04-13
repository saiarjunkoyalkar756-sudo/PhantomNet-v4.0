# install_windows.ps1
# Unified installer script for PhantomNet Agent on Windows 10/11

# --- Configuration ---
$AGENT_DIR = "phantomnet_agent"
$PYTHON_VERSION = "3.11.x" # Specify desired Python version, e.g., 3.11.8
$VENV_DIR = ".venv_phantomnet"
$NOCAP_INSTALLER_URL = "https://npcap.com/dist/npcap-1.78.exe" # Example URL, verify latest
$NOCAP_INSTALLER_PATH = "$env:TEMP\npcap-installer.exe"

$AGENT_SERVICE_NAME = "PhantomNetAgent"
$AGENT_SERVICE_DISPLAY_NAME = "PhantomNet Autonomous Cyber Defense Agent"
$AGENT_SERVICE_DESCRIPTION = "Monitors and defends the endpoint as part of the PhantomNet platform."

$BACKEND_SERVICE_NAME = "PhantomNetBackend"
$BACKEND_SERVICE_DISPLAY_NAME = "PhantomNet Autonomous Cyber Defense Backend"
$BACKEND_SERVICE_DESCRIPTION = "Manages and processes data for the PhantomNet platform."

# --- Functions ---
function Log-Info {
    Param([string]$Message)
    Write-Host "INFO: $Message"
}

function Log-Warn {
    Param([string]$Message)
    Write-Host "WARN: $Message" -ForegroundColor Yellow
}

function Log-Error {
    Param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
    Exit 1
}

function Check-Admin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Log-Error "This script must be run with Administrator privileges."
    }
}

function Install-Python {
    Log-Info "Checking for Python $($PYTHON_VERSION)..."
    try {
        $pythonPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
        if (-not $pythonPath) {
            Log-Warn "Python not found in PATH."
            Log-Error "Please install Python $($PYTHON_VERSION) manually from https://www.python.org/downloads/windows/. Re-run this script after installation."
        }
        
        $pythonVersionOutput = (python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" -ErrorAction SilentlyContinue)
        if ($pythonVersionOutput -ne "3.11") {
            Log-Warn "Detected Python version is $($pythonVersionOutput), but $($PYTHON_VERSION) is recommended."
            Log-Error "Please install Python $($PYTHON_VERSION) manually from https://www.python.org/downloads/windows/. Re-run this script after installation."
        }
    } catch {
        Log-Error "An error occurred while checking Python installation: $($_.Exception.Message). Please ensure Python $($PYTHON_VERSION) is installed manually from https://www.python.org/downloads/windows/."
    }
    Log-Info "Python is installed and detected (version $($pythonVersionOutput))."
}

function Check-VC-Redistributable {
    Log-Info "Checking for Visual C++ Redistributable (needed for many Python packages)..."
    # This check is not exhaustive but covers common versions
    $vcRedistInstalled = Get-ChildItem "HKLM:\SOFTWARE\Classes\Installer\Products" -Recurse | Where-Object { 
        $_.PSChildName -like "00002109*" -and `
        ($_.GetValue("ProductName") -like "*Visual C++ 2015-2022 Redistributable (x64)*" -or `
         $_.GetValue("ProductName") -like "*Visual C++ 2015-2022 Redistributable (x86)*" -or `
         $_.GetValue("ProductName") -like "*Visual C++ 2013 Redistributable (x64)*" -or `
         $_.GetValue("ProductName") -like "*Visual C++ 2013 Redistributable (x86)*")
    }
    if (-not $vcRedistInstalled) {
        Log-Warn "Visual C++ Redistributable is not detected. Many Python packages (especially those with C extensions like 'lxml', 'cryptography', 'scipy', etc.) require it."
        Log-Warn "Please install it manually from Microsoft's website: https://docs.microsoft.com/en-us/cpp/windows/latest-supported-visual-c-downloads"
        Log-Error "Installation cannot proceed without the Visual C++ Redistributable. Please install it and re-run the script."
    }
    Log-Info "Visual C++ Redistributable detected."
}

function Install-Npcap {
    Log-Info "Downloading Npcap installer from $($NOCAP_INSTALLER_URL)..."
    try {
        Invoke-WebRequest -Uri $NOCAP_INSTALLER_URL -OutFile $NOCAP_INSTALLER_PATH -UseBasicParsing
        Log-Info "Npcap installer downloaded. Starting silent installation."
        
        # /S for silent, /npcap_loopback_adapter=no, /winpcap_mode=yes for WinPcap API compatibility
        Start-Process -FilePath $NOCAP_INSTALLER_PATH -ArgumentList "/S /npcap_loopback_adapter=no /winpcap_mode=yes" -Wait -NoNewWindow
        
        if ($LASTEXITCODE -ne 0) {
            Log-Warn "Npcap installation returned non-zero exit code ($LASTEXITCODE). It might have failed or encountered issues. Please verify Npcap installation."
        } else {
            Log-Info "Npcap silent installation initiated. Please check if it installed successfully."
        }
    } catch {
        Log-Warn "Failed to download or install Npcap: $($_.Exception.Message). Please install Npcap manually from npcap.com. Scapy's packet capture will not work without it."
    }
}

function Setup-Python-Env {
    Log-Info "Setting up Python virtual environment..."
    python -m venv $VENV_DIR
    if (-not (Test-Path $VENV_DIR)) {
        Log-Error "Failed to create virtual environment."
    }
    
    # Activate venv for current session - doesn't persist across script blocks in PS easily.
    # We'll use full paths for pip/python within the venv.
    Log-Info "Upgrading pip and installing wheel..."
    & "$PSScriptRoot\$VENV_DIR\Scripts\python.exe" -m pip install --upgrade pip || Log-Error "Failed to upgrade pip."
    & "$PSScriptRoot\$VENV_DIR\Scripts\python.exe" -m pip install wheel || Log-Error "Failed to install wheel."
}

function Install-Python-Deps {
    Log-Info "Installing Python dependencies for the agent (from requirements-windows.txt)..."
    & "$PSScriptRoot\$VENV_DIR\Scripts\python.exe" -m pip install -r "$PSScriptRoot\$AGENT_DIR\requirements-windows.txt" || Log-Error "Failed to install Python dependencies from requirements-windows.txt."
    
    Log-Info "Installing Windows-specific Python libraries (pywin32, wmi)."
    & "$PSScriptRoot\$VENV_DIR\Scripts\python.exe" -m pip install pywin32 wmi || Log-Warn "Failed to install pywin32 or wmi. Some Windows-specific features might be limited."
    
    Log-Info "Attempting to install Scapy and YARA Python bindings."
    & "$PSScriptRoot\$VENV_DIR\Scripts\python.exe" -m pip install scapy || Log-Warn "Scapy installation failed. Network monitoring features may be limited."
    & "$PSScriptRoot\$VENV_DIR\Scripts\python.exe" -m pip install yara-python || Log-Warn "YARA Python installation failed. Memory scanning features may be limited."
}

function Configure-WindowsFirewall {
    Log-Info "Configuring Windows Firewall rules for PhantomNet Agent..."
    # Define ports and executable paths that need to be allowed
    # Example: Allow inbound/outbound for agent's communication port (e.g., 8000 for API)
    # Example: Allow agent's main executable (once PyInstaller is used)

    # Allow outbound traffic for agent (e.g., to Manager/Gateway)
    try {
        # Rule for agent's communication port (example: 8000 for FastAPI/HTTP bus)
        # Assuming agent listens on 8000 for local API or connects outbound on other ports
        New-NetFirewallRule -DisplayName "PhantomNet Agent Outbound" `
            -Direction Outbound -Action Allow -Protocol TCP -LocalPort 8000 `
            -Description "Allow PhantomNet Agent to communicate with Manager/Gateway" `
            -ErrorAction Stop | Out-Null
        
        # Rule for agent executable (once packaged)
        # $AgentExePath = Join-Path $CurrentPath $AGENT_DIR "\phantomnet_agent.exe" # Placeholder for packaged executable
        # New-NetFirewallRule -DisplayName "PhantomNet Agent Executable" `
        #    -Direction Both -Action Allow -Program $AgentExePath `
        #    -Description "Allow PhantomNet Agent executable through firewall" `
        #    -ErrorAction Stop | Out-Null
        
        Log-Info "Windows Firewall rules configured. Review rules if agent communication issues persist."
    } catch {
        Log-Warn "Failed to configure Windows Firewall rules: $($_.Exception.Message). Please configure manually if needed."
    }
}
    
    $CurrentPath = (Get-Item -Path ".\\").FullName
    # Deliverable Note: The long-term goal is to create an MSI or packaged executable (e.g., via PyInstaller).
    # This script currently registers the Python script directly.
    # If a packaged executable were available, $AgentMain would point to that .exe
    # and the service wrapper script would not be needed.
    $PythonExe = Join-Path $CurrentPath $VENV_DIR "\Scripts\python.exe"
    $AgentMain = Join-Path $CurrentPath $AGENT_DIR "\main.py"

    # Create a wrapper script for the service
    $ServiceWrapperScriptPath = Join-Path $CurrentPath $AGENT_DIR "\phantomnet_agent_service.py"
    @'
import subprocess
import sys
import os
import time

# Redirect stdout/stderr to files for logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
STDOUT_PATH = os.path.join(LOG_DIR, "phantomnet_agent_service_stdout.log")
STDERR_PATH = os.path.join(LOG_DIR, "phantomnet_agent_service_stderr.log")

with open(STDOUT_PATH, "a") as stdout_file:
    with open(STDERR_PATH, "a") as stderr_file:
        sys.stdout = stdout_file
        sys.stderr = stderr_file
        print(f"Service wrapper started at {time.ctime()}")
        
        # Define the actual agent command
        # Ensure the path to main.py is correct relative to this wrapper script or absolute
        AGENT_MAIN_PATH = os.path.join(os.path.dirname(__file__), "main.py") 
        
        # Ensure the virtual environment's python is used if possible
        # This wrapper assumes it's run by the venv's python or has the venv activated in its context
        cmd = [sys.executable, AGENT_MAIN_PATH] 
        
        print(f"Executing agent: {' '.join(cmd)}")
        try:
            # Use Popen to keep the process running and detached
            # Consider using creationflags for detaching if this is run directly by SCM
            # For `nssm` or `sc` with `binPath`, this might not need complex detachment here
            process = subprocess.Popen(cmd, cwd=os.path.dirname(AGENT_MAIN_PATH))
            print(f"Agent process started with PID: {process.pid}")
            process.wait() # Wait for the agent to finish (it should run indefinitely)
            print(f"Agent process exited with code: {process.returncode}")
        except Exception as e:
            print(f"Error starting or running agent: {e}", file=sys.stderr)
            
        print(f"Service wrapper ended at {time.ctime()}")
'@ | Set-Content -Path $ServiceWrapperScriptPath
    
    # Using 'sc.exe' to create a Windows service
    # binPath should point to the python.exe inside the venv, which then runs the service wrapper script.
    $BinPath = "`"$PythonExe`" `"$ServiceWrapperScriptPath`""

    Log-Info "Service binPath: $BinPath"

    try {
        # Check if service already exists
        if (Get-Service -Name $AGENT_SERVICE_NAME -ErrorAction SilentlyContinue) {
            Log-Info "Service $($AGENT_SERVICE_NAME) already exists. Updating configuration."
            sc.exe config $AGENT_SERVICE_NAME binPath= "$BinPath" DisplayName= "$AGENT_SERVICE_DISPLAY_NAME" obj= "LocalSystem"
            # Optional: Stop and restart if already running
            # Stop-Service $AGENT_SERVICE_NAME -ErrorAction SilentlyContinue
            # Start-Service $AGENT_SERVICE_NAME -ErrorAction SilentlyContinue
        } else {
            Log-Info "Creating new service $($AGENT_SERVICE_NAME)."
            sc.exe create $AGENT_SERVICE_NAME binPath= "$BinPath" DisplayName= "$AGENT_SERVICE_DISPLAY_NAME" start= "auto" obj= "LocalSystem"
            sc.exe description $AGENT_SERVICE_NAME "$AGENT_SERVICE_DESCRIPTION"
            Log-Info "Service $($AGENT_SERVICE_NAME) created successfully. Set to start automatically."
        }
    } catch {
        Log-Error "Failed to register Windows Service: $($_.Exception.Message)"
    }
}

# --- Main script execution ---
Check-Admin
Install-Python
Check-VC-Redistributable
Install-Npcap
Setup-Python-Env
Install-Python-Deps
Configure-WindowsFirewall
Register-Windows-Service

Log-Info "Windows Agent installation complete. Please review any warnings."
Log-Info "To start the agent service: Start-Service $($AGENT_SERVICE_NAME)"
Log-Info "To stop the agent service: Stop-Service $($AGENT_SERVICE_NAME)"
Log-Info "To check agent service status: Get-Service $($AGENT_SERVICE_NAME)"
Log-Info "Agent logs can be found in $($AGENT_DIR)\logs\phantomnet_agent_service_stdout.log and stderr.log"
Log-Warn "If Scapy or YARA components failed to install, those specific features will be disabled or operate in limited mode."
