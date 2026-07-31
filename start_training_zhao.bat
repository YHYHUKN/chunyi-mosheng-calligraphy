@echo off
chcp 65001 >nul
cd /d "d:\书法春"
echo [%date% %time%] 赵孟頫快速验证 (64px/16batch/10ep)...
set PYTHONUNBUFFERED=1
venv\Scripts\python.exe algorithm\train\run_train_zhao_fast.py > training_output_zhao.txt 2>&1
echo [%date% %time%] 训练结束，退出码: %ERRORLEVEL%
pause
