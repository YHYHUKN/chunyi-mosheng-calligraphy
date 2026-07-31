@echo off
chcp 65001 >nul
echo [%date% %time%] 米芾单风格训练 (128px/30ep/batch8/aug6)...
cd /d "d:\书法春"
venv\Scripts\python.exe algorithm\train\train_mifu.py
echo [%date% %time%] 训练完成
pause
