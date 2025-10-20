# Remote server update script
$SERVER_URL = "http://192.168.51.105:8090"

Write-Host "=========================================="
Write-Host "  Push Update to Server via API"
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

Write-Host ($checkResponse | ConvertTo-Json)
Write-Host ""

if ($checkResponse.has_update) {
    Write-Host "[OK] New version found!" -ForegroundColor Green
    Write-Host "Current version: $($checkResponse.current_version)"
    Write-Host "Commits behind: $($checkResponse.commits_behind)"
    Write-Host ""

    # Step 3: Execute update
    Write-Host "=== 3. Executing update ==="
    $updateBody = '{"use_proxy": false, "auto_restart": true}'
    
    try {
        $updateResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/update" -Method Post -ContentType "application/json" -Body $updateBody
        Write-Host ($updateResponse | ConvertTo-Json)
        Write-Host ""

        if ($updateResponse.updated) {
            Write-Host "[OK] Update successful!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Waiting for service restart..."
            Start-Sleep -Seconds 10

            # Step 4: Verify service
            Write-Host "=== 4. Verifying service status ==="
            for ($i = 1; $i -le 5; $i++) {
                try {
                    $null = Invoke-WebRequest -Uri $SERVER_URL -Method Head -TimeoutSec 5 -ErrorAction Stop
                    Write-Host "[OK] Service is back online" -ForegroundColor Green
                    break
                } catch {
                    Write-Host "Waiting for service... ($i/5)"
                    Start-Sleep -Seconds 3
                }
            }
        } else {
            Write-Host "[ERROR] Update failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "[ERROR] Update request failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        
        $forceUpdate = Read-Host "Try force update? (y/n)"
        if ($forceUpdate -eq "y") {
            Write-Host ""
            Write-Host "=== Executing force update ==="
            $forceBody = '{"use_proxy": false, "auto_restart": true}'
            
            try {
                $forceResponse = Invoke-RestMethod -Uri "$SERVER_URL/api/force-update" -Method Post -ContentType "application/json" -Body $forceBody
                Write-Host ($forceResponse | ConvertTo-Json)
                Write-Host ""

                if ($forceResponse.updated) {
                    Write-Host "[OK] Force update successful!" -ForegroundColor Green
                    Start-Sleep -Seconds 10
                } else {
                    Write-Host "[ERROR] Force update failed" -ForegroundColor Red
                }
            } catch {
                Write-Host "[ERROR] Force update request failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
} else {
    Write-Host "[INFO] Already up to date" -ForegroundColor Cyan
    Write-Host "Current version: $($checkResponse.current_version)"
}

Write-Host ""
Write-Host "=========================================="
Write-Host "  Operation Complete"
Write-Host "=========================================="
Write-Host ""
Write-Host "Please refresh your browser (Ctrl+Shift+R)"
Write-Host ""
