@echo off
chcp 65001 >nul
echo ============================================
echo   春意墨生 - AI书法模型训练
echo   GPU: RTX 3050 4GB
echo   预计时长: ~1.6 小时
echo ============================================
echo.

cd /d d:\书法春
venv\Scripts\python algorithm\train\run_train.py

echo.
echo ============================================
echo   训练完成！
echo ============================================
pause
