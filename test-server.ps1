# Test server connectivity
$servers = @(
    "http://192.168.51.100:8090",
    "http://localhost:8090",
    "http://127.0.0.1:8090"
)

Write-Host "Testing server connectivity..."
Write-Host ""

foreach ($server in $servers) {
    Write-Host "Testing: $server"
    try {
        $response = Invoke-WebRequest -Uri $server -Method Head -TimeoutSec 3 -ErrorAction Stop
        Write-Host "  [OK] Server is reachable" -ForegroundColor Green
        Write-Host "  Status: $($response.StatusCode)"
        Write-Host ""
    } catch {
        Write-Host "  [FAIL] Cannot reach server" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host ""
    }
}

Write-Host "Please provide the correct server URL if none of the above worked."
