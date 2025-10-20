# Fix server script - diagnose and restart service
$SERVER_URL = "http://192.168.51.105:8090"

Write-Host "=========================================="
Write-Host "  Server Diagnostic and Fix"
Write-Host "=========================================="
Write-Host ""

# Step 1: Check server status
Write-Host "=== 1. Checking server status ==="
try {
    $response = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] Server is responding" -ForegroundColor Green
    Write-Host "Status: $($response.StatusCode)"
} catch {
    Write-Host "[ERROR] Server is not responding" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)"
}
Write-Host ""

# Step 2: SSH to server and check/restart service
Write-Host "=== 2. Connecting to server to restart service ==="
Write-Host ""
Write-Host "Please run these commands on your server:" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Check if service is running" -ForegroundColor Cyan
Write-Host "ps aux | grep 'python3 app.py'"
Write-Host ""
Write-Host "# Check recent logs" -ForegroundColor Cyan
Write-Host "cd ~/media-sorter && tail -50 app.log"
Write-Host ""
Write-Host "# Kill any stuck processes" -ForegroundColor Cyan
Write-Host "pkill -9 -f 'python3 app.py'"
Write-Host ""
Write-Host "# Restart service" -ForegroundColor Cyan
Write-Host "cd ~/media-sorter && nohup python3 app.py > app.log 2>&1 &"
Write-Host ""
Write-Host "# Verify service started" -ForegroundColor Cyan
Write-Host "sleep 3 && curl -I http://localhost:8090"
Write-Host ""

Write-Host "=========================================="
Write-Host "  Or use this one-liner:"
Write-Host "=========================================="
Write-Host ""
Write-Host "cd ~/media-sorter && pkill -9 -f 'python3 app.py' && sleep 2 && nohup python3 app.py > app.log 2>&1 & && sleep 3 && curl -I http://localhost:8090" -ForegroundColor Green
Write-Host ""
