@echo off
chcp 65001 >nul
echo [%date% %time%] 开始切割阴符经(连通域法)...
cd /d "d:\书法春"
venv\Scripts\python.exe algorithm\data\cut_yinjing_fast.py
echo [%date% %time%] 切割完成
pause
