# stop_grid.ps1
# Instantly terminates all PhantomNet microservice processes

Write-Host "`n--- PhantomNet Process Termination ---" -ForegroundColor Yellow

# Ports utilized by the Gateway and IAM services
$targetPorts = 8000, 8002

foreach ($port in $targetPorts) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.OwningProcess -gt 4) {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                try {
                    Write-Host "--> Terminating session on Port $port (PID: $($proc.Id))..." -ForegroundColor Gray
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                } catch {
                    # No-op for protected processes
                }
            }
        }
    }
}

Write-Host "--- Grid Successfully Neutralized ---" -ForegroundColor Green
