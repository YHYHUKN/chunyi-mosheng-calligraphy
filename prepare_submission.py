"""
打包提交用：复制核心文件到 submission/ 目录
"""
import os
import shutil
from pathlib import Path

SRC = Path("D:/书法春")
DST = Path("D:/书法春/submission")

# 1. 复制前端文件
print("[] 复制前端文件...")
shutil.copy(SRC / "index.html", DST / "index.html")
if (SRC / "assets").exists():
    if (DST / "assets").exists():
        shutil.rmtree(DST / "assets")
    shutil.copytree(SRC / "assets", DST / "assets")
print("   前端文件完成")

# 2. 复制后端服务代码（不含训练数据）
print("[] 复制后端代码...")
server_src = SRC / "algorithm" / "server"
server_dst = DST / "algorithm" / "server"
if server_dst.exists():
    shutil.rmtree(server_dst)
shutil.copytree(server_src, server_dst)
print("   后端代码完成")

# 3. 复制书法字库（全部5000+文件，这是核心数据）
print("[] 复制书法字库（可能较慢，请等待）...")
src_font = SRC / "书法字库"
dst_font = DST / "书法字库"
if dst_font.exists():
    shutil.rmtree(dst_font)
shutil.copytree(src_font, dst_font)
print(f"   书法字库完成，共 {sum(1 for _ in dst_font.rglob('*'))} 个文件")

# 4. 复制最新 checkpoint（只复制最新的那个，减小体积）
print("[] 复制模型checkpoint...")
ckpt_src = SRC / "checkpoints"
ckpt_dst = DST / "checkpoints"
if ckpt_dst.exists():
    shutil.rmtree(ckpt_dst)
ckpt_dst.mkdir(exist_ok=True)

# 只复制最新的 .pth 文件（通常 best_ckpt.pth 或 epoch_60.pth）
important_ckpts = ["best_ckpt.pth", "epoch_60.pth", "epoch_50.pth"]
for ckpt_name in important_ckpts:
    src_file = ckpt_src / ckpt_name
    if src_file.exists():
        shutil.copy(src_file, ckpt_dst / ckpt_name)
        size_mb = src_file.stat().st_size / (1024*1024)
        print(f"   已复制 {ckpt_name} ({size_mb:.1f} MB)")

# 5. 复制项目说明文档
print("[] 复制说明文档...")
for doc in ["使用说明.md", "项目代码说明书.md", "春意墨生AI书法创作系统_使用说明.docx"]:
    src_file = SRC / doc
    if src_file.exists():
        shutil.copy(src_file, DST / doc)
        print(f"   已复制 {doc}")

# 6. 复制 package.json
shutil.copy(SRC / "package.json", DST / "package.json")
print("   package.json 完成")

# 7. 生成 requirements.txt
print("[] 生成 requirements.txt...")
requirements = [
    "fastapi==0.104.1",
    "uvicorn==0.24.0",
    "torch==2.1.0",
    "torchvision==0.16.0",
    "opencv-python==4.8.1.78",
    "Pillow==10.1.0",
    "numpy==1.26.2",
    "python-multipart==0.0.6",
]
with open(DST / "requirements.txt", "w", encoding="utf-8") as f:
    f.write("# 春意墨生AI书法创作系统 - Python依赖\n")
    f.write("# 安装命令: pip install -r requirements.txt\n")
    f.write("\n".join(requirements))
    f.write("\n")
print("   requirements.txt 完成")

print("\n" + "="*50)
print("核心文件复制完成！")
print(f"提交包路径: {DST}")
print("接下来运行第2步：生成 README 和压缩包")
