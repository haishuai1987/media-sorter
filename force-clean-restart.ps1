# Multiple force updates to ensure clean restart
$SERVER_URL = "http://192.168.51.105:8090"

Write-Host "=== Multiple Force Updates ===" -ForegroundColor Cyan

for ($i = 1; $i -le 3; $i++) {
    Write-Host "`nAttempt $i/3..." -ForegroundColor Yellow
    
    $body = '{"use_proxy": false, "auto_restart": true}'
    try {
        $response = Invoke-RestMethod -Uri "$SERVER_URL/api/force-update" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 10
        Write-Host "  Response: $($response.message)" -ForegroundColor Green
    } catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    if ($i -lt 3) {
        Write-Host "  Waiting 15 seconds..." -ForegroundColor Gray
        Start-Sleep -Seconds 15
    }
}

Write-Host "`nWaiting 10 seconds for final restart..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`nChecking service..." -ForegroundColor Yellow
for ($i = 1; $i -le 5; $i++) {
    try {
        $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
        Write-Host "[OK] Service is online!" -ForegroundColor Green
        break
    } catch {
        Write-Host "Waiting... ($i/5)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

Write-Host "`nDone! Please test again." -ForegroundColor Cyan
