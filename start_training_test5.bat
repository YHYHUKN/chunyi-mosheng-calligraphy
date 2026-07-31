@echo off
chcp 65001 >nul
cd /d "d:\书法春"
echo [%date% %time%] 修复后测试训练 (5 epochs)...
set PYTHONUNBUFFERED=1
venv\Scripts\python.exe algorithm\train\run_train.py > training_output_test5.txt 2>&1
echo [%date% %time%] 测试训练结束，退出码: %ERRORLEVEL%
pause
