@echo off
echo ========================================
echo   手势贪吃蛇游戏 - Web 版启动脚本
echo ========================================
echo.

echo [1/2] 检查依赖...
D:\anaconda3\envs\env_mediapipe\python.exe -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装 Web 依赖...
    D:\anaconda3\envs\env_mediapipe\python.exe -m pip install -r requirements.txt
) else (
    echo ✓ 依赖已安装
)

echo.
echo [2/2] 启动 Flask 服务器...
echo.
echo ========================================
echo   服务器启动后，请在浏览器访问：
echo   http://localhost:5000
echo ========================================
echo.
echo 按 Ctrl+C 停止服务器
echo.

D:\anaconda3\envs\env_mediapipe\python.exe app.py

pause
