# Simple restart script
$SERVER_URL = "http://192.168.51.105:8090"

Write-Host "Restarting server..." -ForegroundColor Cyan

# Force update to ensure latest code
$forceBody = '{"use_proxy": false, "auto_restart": true}'
try {
    $response = Invoke-RestMethod -Uri "$SERVER_URL/api/force-update" -Method Post -ContentType "application/json" -Body $forceBody -ErrorAction Stop
    Write-Host "Update response: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "Update failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host "Waiting 10 seconds for restart..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Check service
for ($i = 1; $i -le 5; $i++) {
    try {
        $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[OK] Service is online" -ForegroundColor Green
        break
    } catch {
        Write-Host "Waiting... ($i/5)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

Write-Host "Done!" -ForegroundColor Green
