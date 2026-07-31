@echo off
chcp 65001 >nul
cd /d "d:\书法春"
echo [%date% %time%] 开始训练...
venv\Scripts\python.exe algorithm\train\run_train.py > training_output_new.txt 2>&1
echo [%date% %time%] 训练结束，退出码: %ERRORLEVEL%
