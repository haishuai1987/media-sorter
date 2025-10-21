@echo off
chcp 65001 >nul
REM 更新服务器到v1.2.4

echo ==========================================
echo   更新服务器到 v1.2.4
echo ==========================================
echo.

set SERVER=192.168.51.105
set USER=haishuai
set PASSWORD=China1987

echo 🔗 连接到服务器 %SERVER%...
echo 用户: %USER%
echo.

REM 使用plink（如果安装了PuTTY）
where plink >nul 2>&1
if %errorlevel% equ 0 (
    echo 使用plink连接...
    echo %PASSWORD%| plink -ssh -l %USER% -pw %PASSWORD% %SERVER% "cd /root/media-renamer && git pull origin main && cat version.txt && pkill -f 'python.*app.py' && sleep 2 && nohup python3 app.py > app.log 2>&1 & && sleep 3 && ps aux | grep 'python.*app.py' | grep -v grep && tail -20 app.log"
    goto :done
)

REM 如果没有plink，提示手动操作
echo ⚠️ 未找到plink工具
echo.
echo 请手动执行以下步骤：
echo.
echo 1. 打开PuTTY或其他SSH客户端
echo 2. 连接到: %SERVER%
echo 3. 用户名: %USER%
echo 4. 密码: %PASSWORD%
echo.
echo 5. 执行以下命令：
echo    cd /root/media-renamer
echo    git pull origin main
echo    cat version.txt
echo    pkill -f "python.*app.py"
echo    sleep 2
echo    nohup python3 app.py ^> app.log 2^>^&1 ^&
echo    sleep 3
echo    ps aux ^| grep "python.*app.py" ^| grep -v grep
echo.

:done
echo.
echo ==========================================
echo   更新完成
echo ==========================================
echo.
pause
