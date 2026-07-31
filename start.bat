@echo off
chcp 65001 >nul
title 春意墨生 - AI书法创作系统

echo ═══════════════════════════════════════════════
echo    春意墨生 - AI书法创作系统
echo    基于GAN与风格解耦技术
echo ═══════════════════════════════════════════════
echo.

cd /d "%~dp0"

:: 检查虚拟环境
if not exist "venv\Scripts\python.exe" (
    echo [信息] 首次运行，正在创建虚拟环境...
    py -3 -m venv venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败，请确保已安装 Python 3.10+
        pause
        exit /b 1
    )
    echo [信息] 正在安装依赖（首次可能需要几分钟）...
    venv\Scripts\pip.exe install torch torchvision --index-url https://download.pytorch.org/whl/cpu -q
    venv\Scripts\pip.exe install fastapi uvicorn python-multipart opencv-python-headless pydantic -q
    echo [信息] 依赖安装完成！
    echo.
)

echo [启动] 正在启动AI书法创作系统...
echo [访问] 请在浏览器打开: http://localhost:8080
echo [停止] 按 Ctrl+C 停止服务
echo.

:: 启动FastAPI服务
venv\Scripts\python.exe -u algorithm\server\app.py

pause
