# Force restart with cache cleaning
$SERVER_URL = "http://192.168.51.105:8090"

Write-Host "=== Force Restart with Cache Cleaning ===" -ForegroundColor Cyan

# Step 1: Trigger force update
Write-Host "`n1. Triggering force update..." -ForegroundColor Yellow
$body = '{"use_proxy": false, "auto_restart": false}'
try {
    $response = Invoke-RestMethod -Uri "$SERVER_URL/api/force-update" -Method Post -ContentType "application/json" -Body $body
    Write-Host "   Update: $($response.message)" -ForegroundColor Green
} catch {
    Write-Host "   Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n2. Waiting 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 2: Kill all Python processes
Write-Host "`n3. Stopping all Python processes..." -ForegroundColor Yellow
$killBody = '{"command": "pkill -9 -f python"}'
try {
    Invoke-RestMethod -Uri "$SERVER_URL/api/execute-command" -Method Post -ContentType "application/json" -Body $killBody -ErrorAction SilentlyContinue
} catch {
    Write-Host "   Process killed (expected)" -ForegroundColor Gray
}

Write-Host "`n4. Waiting 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Step 3: Start service with cache clearing
Write-Host "`n5. Starting service with clean cache..." -ForegroundColor Yellow
$startBody = '{"command": "cd /root/media-sorter && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; nohup python3 -B app.py > /dev/null 2>&1 &"}'
try {
    Invoke-RestMethod -Uri "$SERVER_URL/api/execute-command" -Method Post -ContentType "application/json" -Body $startBody -ErrorAction SilentlyContinue
} catch {
    Write-Host "   Command sent" -ForegroundColor Gray
}

Write-Host "`n6. Waiting 10 seconds for service to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Step 4: Check service
Write-Host "`n7. Checking service status..." -ForegroundColor Yellow
for ($i = 1; $i -le 5; $i++) {
    try {
        $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
        Write-Host "   [OK] Service is online!" -ForegroundColor Green
        break
    } catch {
        Write-Host "   Waiting... ($i/5)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "Please refresh your browser and test again." -ForegroundColor Green
