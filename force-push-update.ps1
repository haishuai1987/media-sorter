# Force update script - automatically uses force update if normal update fails
$SERVER_URL = "http://192.168.51.105:8090"

Write-Host "=========================================="
Write-Host "  Force Push Update to Server"
Write-Host "=========================================="
Write-Host ""

# Step 1: Check server status
Write-Host "=== 1. Checking server status ==="
try {
    $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[OK] Server is online" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Server is offline or unreachable" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Check for updates
Write-Host "=== 2. Checking for updates ==="
$checkBody = '{"use_proxy": false}'
$checkResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/check-update" -Method Post -ContentType "application/json" -Body $checkBody

Write-Host "Current version: $($checkResponse.current_version)"
Write-Host "Has update: $($checkResponse.has_update)"
if ($checkResponse.has_update) {
    Write-Host "Commits behind: $($checkResponse.commits_behind)" -ForegroundColor Yellow
}
Write-Host ""

if ($checkResponse.has_update) {
    # Step 3: Try normal update first
    Write-Host "=== 3. Trying normal update ==="
    $updateBody = '{"use_proxy": false, "auto_restart": true}'
    
    try {
        $updateResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/update" -Method Post -ContentType "application/json" -Body $updateBody -ErrorAction Stop
        
        if ($updateResponse.updated) {
            Write-Host "[OK] Normal update successful!" -ForegroundColor Green
            Write-Host "Message: $($updateResponse.message)"
        } else {
            throw "Update failed: $($updateResponse.error)"
        }
    } catch {
        Write-Host "[WARN] Normal update failed: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host ""
        
        # Step 4: Execute force update
        Write-Host "=== 4. Executing FORCE update ==="
        $forceBody = '{"use_proxy": false, "auto_restart": true}'
        
        try {
            $forceResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/force-update" -Method Post -ContentType "application/json" -Body $forceBody -ErrorAction Stop
            
            if ($forceResponse.updated) {
                Write-Host "[OK] Force update successful!" -ForegroundColor Green
                Write-Host "Message: $($forceResponse.message)"
            } else {
                Write-Host "[ERROR] Force update failed: $($forceResponse.error)" -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "[ERROR] Force update request failed: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host ""
    Write-Host "Waiting for service restart (10 seconds)..."
    Start-Sleep -Seconds 10
    
    # Step 5: Verify service
    Write-Host ""
    Write-Host "=== 5. Verifying service status ==="
    $serviceUp = $false
    for ($i = 1; $i -le 5; $i++) {
        try {
            $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
            Write-Host "[OK] Service is back online" -ForegroundColor Green
            $serviceUp = $true
            break
        } catch {
            Write-Host "Waiting for service... ($i/5)"
            Start-Sleep -Seconds 3
        }
    }
    
    if (-not $serviceUp) {
        Write-Host "[WARN] Service may need more time to start" -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] Already up to date - no update needed" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=========================================="
Write-Host "  Operation Complete"
Write-Host "=========================================="
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Refresh your browser (Ctrl+Shift+R)"
Write-Host "  2. Check 'Current Version' in settings"
Write-Host ""
