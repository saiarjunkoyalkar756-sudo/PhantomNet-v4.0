# 1. Standardize Project Environment & Cleanup
$Root = Get-Location
$Env:PYTHONPATH = "$Root;$Env:PYTHONPATH"
$Env:ENVIRONMENT = "production"
$Env:JWT_SECRET_KEY = "HARDENED_LOCAL_KEY_$(Get-Random)"
$Env:DB_PASSWORD = "LOCAL_MOCK_PASSWORD"
$Env:NEO4J_PASSWORD = "LOCAL_MOCK_PASSWORD"
$Env:REDIS_PASSWORD = "LOCAL_MOCK_PASSWORD"

Write-Host "`n--- PhantomNet Operational Cleanup ---" -ForegroundColor Yellow
# Kill any existing processes on the required ports
Get-NetTCPConnection -LocalPort 8000, 8002 -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.OwningProcess -gt 4) {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            try {
                Write-Host "--> Releasing Port $($_.LocalPort) from PID $($proc.Id)..." -ForegroundColor Gray
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            } catch {
                Write-Host "(!) Failed to stop PID $($proc.Id). Access denied or process closed." -ForegroundColor Red
            }
        }
    }
}
Start-Sleep -Seconds 1

Write-Host "`n--- PhantomNet Absolute Grid Stabilization (Phase 14) ---" -ForegroundColor Cyan

# 2. Comprehensive Dependency Verification
Write-Host "[1/4] Verifying exhaustive dependency manifest..." -ForegroundColor Yellow
$core_libs = "fastapi", "uvicorn", "loguru", "numpy", "pandas", "pydantic_settings", "docker", "kafka", "web3", "solcx", "transformers", "yara", "nmap", "stix2", "lark", "fpdf", "aiofiles"
$missing = $false

foreach ($lib in $core_libs) {
    # Check each library individually to pinpoint missing ones
    python -c "import $lib" 2>$null
    if ($lastExitCode -ne 0) {
        Write-Host "(!) Missing dependency detected: $lib" -ForegroundColor Gray
        $missing = $true
    }
}

if ($missing) {
    Write-Host "(!) One or more module blockers detected. Initializing Absolute Sync..." -ForegroundColor Magenta
    
    # Step A: Upgrade Pip
    Write-Host "--> Upgrading Pip to latest version..." -ForegroundColor Gray
    python -m pip install --upgrade pip
    
    # Step B: Install the Ultimate Manifest
    Write-Host "--> Installing exhaustive 40+ dependency manifest (Python 3.13 Binary Only)..." -ForegroundColor Gray
    python -m pip install --prefer-binary -r backend_api/requirements.txt
    
    if ($lastExitCode -ne 0) {
        Write-Error "`n[CRITICAL ERROR] Dependency synchronization failed."
        Write-Host "Please manualy run: pip install --only-binary=:all: -r backend_api/requirements.txt" -ForegroundColor Cyan
        exit
    }
}

# 3. Launching Hardened Micro-Services (Selection 1: Core + AI + Defense)
# Stage 1: CORE (Ingestion and Security)
$core_services = [ordered]@{
    "Ingestor"   = @{ "port" = 8000; "module" = "backend_api.telemetry_ingestor.main" };
    "Gateway"    = @{ "port" = 8001; "module" = "backend_api.gateway_service.main" };
    "IAM Node"   = @{ "port" = 8002; "module" = "backend_api.iam_service.main" };
    "Normalizer" = @{ "port" = 8003; "module" = "backend_api.event_normalizer.main" }
}

# Stage 2: INTEL (AI Analysis)
$intel_services = [ordered]@{
    "UEBA Engine" = @{ "port" = 8004; "module" = "backend_api.ai_behavioral_engine.main" };
    "Graph Intel" = @{ "port" = 8007; "module" = "backend_api.graph_intelligence_service.main" };
    "Threat Intel"= @{ "port" = 8015; "module" = "backend_api.threat_intelligence_service.main" }
}

# Stage 3: ACTION (Automation and Defense)
$action_services = [ordered]@{
    "SOAR Engine" = @{ "port" = 8016; "module" = "backend_api.soar_playbook_engine.main" };
    "Auto Resp"   = @{ "port" = 8018; "module" = "backend_api.auto_response_engine.main" };
    "BAS Engine"  = @{ "port" = 8028; "module" = "backend_api.bas_engine.main" };
    "Blue Team"   = @{ "port" = 8029; "module" = "backend_api.autonomous_blue_team.main" };
    "Orchestrator"= @{ "port" = 8030; "module" = "backend_api.ai_agent_orchestrator.main" }
}

function Start-GridService($name, $port, $module) {
    Write-Host "[WAIT] Initializing $name on Port $port..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit -Command cd $Root; `$Env:PYTHONPATH='$Root'; `$Env:JWT_SECRET_KEY='$($Env:JWT_SECRET_KEY)'; `$Env:DB_PASSWORD='$($Env:DB_PASSWORD)'; `$Env:NEO4J_PASSWORD='$($Env:NEO4J_PASSWORD)'; `$Env:REDIS_PASSWORD='$($Env:REDIS_PASSWORD)'; python -m uvicorn $module`:app --port $port"
}

Write-Host "`n--- Initializing Stage 1: Core Services ---" -ForegroundColor Cyan
foreach ($key in $core_services.Keys) { Start-GridService $key $core_services[$key].port $core_services[$key].module }
Start-Sleep -Seconds 3

Write-Host "`n--- Initializing Stage 2: Intelligence Layer ---" -ForegroundColor Cyan
foreach ($key in $intel_services.Keys) { Start-GridService $key $intel_services[$key].port $intel_services[$key].module }
Start-Sleep -Seconds 3

Write-Host "`n--- Initializing Stage 3: Defensive Actions ---" -ForegroundColor Cyan
foreach ($key in $action_services.Keys) { Start-GridService $key $action_services[$key].port $action_services[$key].module }

Write-Host "`n--- Absolute Grid Verification Active ---" -ForegroundColor Yellow
Write-Host "Central Node: http://localhost:8001"
Write-Host "Grid Status: 12 services in sequence boot."
Write-Host "All platform guards (PQC, Bio-Fusion, AI Consensus) are now initializing."
