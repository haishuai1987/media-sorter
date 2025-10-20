#!/bin/bash

# 远程服务器信息
SERVER_URL="http://192.168.51.100:8090"

echo "=========================================="
echo "  通过 API 推送更新到服务器"
echo "=========================================="
echo ""

echo "=== 1. 检查服务器状态 ==="
if curl -s -f -I "$SERVER_URL" > /dev/null 2>&1; then
    echo "✅ 服务器在线"
else
    echo "❌ 服务器离线或无法访问"
    exit 1
fi
echo ""

echo "=== 2. 检查是否有更新 ==="
CHECK_RESPONSE=$(curl -s -X POST "$SERVER_URL/api/check-update" \
    -H "Content-Type: application/json" \
    -d '{"use_proxy": false}')

echo "$CHECK_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$CHECK_RESPONSE"
echo ""

# 解析响应
HAS_UPDATE=$(echo "$CHECK_RESPONSE" | grep -o '"has_update":[^,}]*' | cut -d':' -f2 | tr -d ' ')

if [ "$HAS_UPDATE" = "true" ]; then
    echo "✅ 发现新版本！"
    echo ""
    
    echo "=== 3. 执行更新 ==="
    UPDATE_RESPONSE=$(curl -s -X POST "$SERVER_URL/api/update" \
        -H "Content-Type: application/json" \
        -d '{"use_proxy": false, "auto_restart": true}')
    
    echo "$UPDATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPDATE_RESPONSE"
    echo ""
    
    # 检查更新是否成功
    if echo "$UPDATE_RESPONSE" | grep -q '"updated".*true'; then
        echo "✅ 更新成功！"
        echo ""
        echo "⏳ 等待服务重启..."
        sleep 10
        
        echo "=== 4. 验证服务状态 ==="
        for i in {1..5}; do
            if curl -s -f -I "$SERVER_URL" > /dev/null 2>&1; then
                echo "✅ 服务已恢复正常"
                break
            else
                echo "⏳ 等待服务启动... ($i/5)"
                sleep 3
            fi
        done
    else
        echo "❌ 更新失败"
        echo ""
        echo "💡 尝试强制更新？(y/n)"
        read -r FORCE_UPDATE
        
        if [ "$FORCE_UPDATE" = "y" ] || [ "$FORCE_UPDATE" = "Y" ]; then
            echo ""
            echo "=== 执行强制更新 ==="
            FORCE_RESPONSE=$(curl -s -X POST "$SERVER_URL/api/force-update" \
                -H "Content-Type: application/json" \
                -d '{"use_proxy": false, "auto_restart": true}')
            
            echo "$FORCE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$FORCE_RESPONSE"
            echo ""
            
            if echo "$FORCE_RESPONSE" | grep -q '"updated".*true'; then
                echo "✅ 强制更新成功！"
                echo ""
                echo "⏳ 等待服务重启..."
                sleep 10
                
                echo "=== 验证服务状态 ==="
                for i in {1..5}; do
                    if curl -s -f -I "$SERVER_URL" > /dev/null 2>&1; then
                        echo "✅ 服务已恢复正常"
                        break
                    else
                        echo "⏳ 等待服务启动... ($i/5)"
                        sleep 3
                    fi
                done
            else
                echo "❌ 强制更新失败"
            fi
        fi
    fi
else
    echo "ℹ️  已是最新版本，无需更新"
fi

echo ""
echo "=========================================="
echo "  操作完成"
echo "=========================================="
echo ""
echo "📝 提示："
echo "   - 请在浏览器中按 Ctrl+Shift+R 强制刷新页面"
echo "   - 检查'系统更新配置'中的'当前版本'是否正常显示"
echo ""
