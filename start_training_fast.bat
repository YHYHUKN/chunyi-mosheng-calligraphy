@echo off
chcp 65001 >nul
cd /d "d:\书法春"
echo [%date% %time%] 快速验证训练 (128px, 15 epochs, batch 16)...
set PYTHONUNBUFFERED=1
venv\Scripts\python.exe algorithm\train\run_train_fast.py > training_output_fast.txt 2>&1
echo [%date% %time%] 快速训练结束，退出码: %ERRORLEVEL%
pause
