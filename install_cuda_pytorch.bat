@echo off
echo ============================================
echo  安装 PyTorch CUDA 版本（用于 RTX 3050）
echo  预计下载 2-3GB，需要几分钟
echo ============================================
echo.

d:\书法春\venv\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --force-reinstall --no-deps

echo.
echo 安装完成，验证 CUDA...
d:\书法春\venv\Scripts\python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

echo.
pause
