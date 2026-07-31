# -*- coding: utf-8 -*-
"""检查云墨济心数据集中6种目标风格的数据质量"""
import sys, os
from pathlib import Path
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r"D:\书法春\书法字库\Calli-Tongji\Calli-Tongji")

# 我们的6种目标风格
TARGETS = {
    "米芾": "行",
    "赵孟頫": "楷",
    "褚遂良": "楷",
    "乙瑛碑": "隶",
    "邓石如": "篆",
    "怀素": "草",
}

# 模型配置
TARGET_SIZE = 128

print("=" * 70)
print("  云墨济心数据集 - 6种目标风格质量检查")
print("=" * 70)

total_match = 0
total_extra = 0

for name, script in TARGETS.items():
    # 查找匹配目录
    dir_name = f"{name}-{script}"
    dir_path = BASE / dir_name
    
    if not dir_path.exists():
        # 尝试模糊匹配
        found = False
        for d in BASE.iterdir():
            if d.is_dir() and name in d.name:
                dir_path = d
                dir_name = d.name
                found = True
                break
        if not found:
            print(f"\n❌ [{name}-{script}] 未找到匹配目录!")
            continue
    
    pngs = list(dir_path.glob("*.png"))
    print(f"\n{'─' * 60}")
    print(f"✅ [{name}] 匹配目录: {dir_name}")
    print(f"   图片数量: {len(pngs)}")
    total_match += len(pngs)
    
    # 检查图片质量
    sizes = []
    ratios = []
    white_pcts = []
    dark_pcts = []
    
    for f in pngs[:10]:  # 抽检前10张
        try:
            img = Image.open(f)
            w, h = img.size
            sizes.append((w, h))
            ratios.append(w / h)
            
            # 灰度分析
            gray = np.array(img.convert("L"))
            white_pcts.append((gray > 200).sum() / gray.size)
            dark_pcts.append((gray < 60).sum() / gray.size)
        except Exception as e:
            print(f"   ⚠ {f.name}: 读取失败 {e}")
    
    if sizes:
        unique_sizes = set(sizes)
        print(f"   图片尺寸: {unique_sizes if len(unique_sizes) <= 3 else f'{len(unique_sizes)}种不同尺寸'}")
        print(f"   样例尺寸: {sizes[0]}")
        
        avg_white = np.mean(white_pcts)
        avg_dark = np.mean(dark_pcts)
        print(f"   白色像素: {avg_white:.1%}")
        print(f"   黑色像素: {avg_dark:.1%}")
        
        # 质量评估
        if avg_white > 0.98:
            print(f"   ⚠ 警告: 图片几乎全白，可能质量有问题")
        elif avg_white > 0.9:
            print(f"   ⚠ 注意: 背景白色占比较高，字较小")
        else:
            print(f"   ✅ 质量: 笔画占比合理")

        # 宽高比检查
        avg_ratio = np.mean(ratios)
        if 0.8 <= avg_ratio <= 1.2:
            print(f"   ✅ 宽高比: {avg_ratio:.2f} (接近正方形)")
        else:
            print(f"   ⚠ 宽高比: {avg_ratio:.2f} (非正方形，需裁切)")

# 统计额外可用数据
print(f"\n{'=' * 60}")
print(f"\n📌 可直接匹配的6种风格: {total_match} 张")

# 找额外可用的同书体数据
print(f"\n📌 额外可利用的同书体数据:")
for script in ["楷", "行", "隶", "篆", "草"]:
    dirs = [d for d in BASE.iterdir() if d.is_dir() and d.name.endswith(f"-{script}")]
    count = sum(len(list(d.glob("*.png"))) for d in dirs)
    names = [d.name.split("-")[0] for d in dirs]
    print(f"   {script}书: {len(dirs)}位书家, {count}张")
    print(f"      书家: {', '.join(names[:10])}{'...' if len(names) > 10 else ''}")
    total_extra += count

print(f"\n{'=' * 60}")
print(f"📊 总结:")
print(f"   6种目标风格: {total_match} 张 (每种100张)")
print(f"   全部同书体数据: {total_match + total_extra} 张")
print(f"   全部50类数据: {sum(len(list(d.glob('*.png'))) for d in BASE.iterdir() if d.is_dir())} 张")

# 检查dataset.txt
ds_txt = BASE / "dataset.txt"
if ds_txt.exists():
    with open(ds_txt, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"\n   dataset.txt: {len(lines)} 条记录")
    # 找包含目标书法家的行
    print(f"\n📌 dataset.txt中6位书法家相关条目:")
    for line in lines:
        for name in TARGETS.keys():
            if name in line:
                print(f"   {line.strip()}")
