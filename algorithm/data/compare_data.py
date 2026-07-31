"""检查第二次训练数据（现在加载的60 epoch模型用的数据备份）的质量"""
import sys, os, glob
from PIL import Image
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')

backup = r'd:\书法春\algorithm\data\_backup_font_render'
current = r'd:\书法春\algorithm\data'

print("=" * 60)
print("第二次训练数据备份 (_backup_font_render)")
print("=" * 60)
for style in ['米芾', '赵孟頫', '褚遂良', '乙瑛碑', '邓石如', '怀素']:
    dir_path = os.path.join(backup, style)
    if not os.path.exists(dir_path):
        print(f"\n{style}: 目录不存在!")
        continue
    files = glob.glob(os.path.join(dir_path, '*.*'))
    print(f"\n{style}: {len(files)} 张")
    # 检查前3张
    for f in files[:3]:
        img = Image.open(f)
        arr = np.array(img)
        white_pct = (arr > 240).sum() / arr.size * 100
        print(f"  {os.path.basename(f)}: {img.size}, mode={img.mode}, 白像素={white_pct:.1f}%")

print("\n" + "=" * 60)
print("当前训练数据（第三次训练用的）")
print("=" * 60)
for style in ['米芾', '赵孟頫', '褚遂良', '乙瑛碑', '邓石如', '怀素']:
    dir_path = os.path.join(current, style)
    if not os.path.exists(dir_path):
        print(f"\n{style}: 目录不存在!")
        continue
    files = glob.glob(os.path.join(dir_path, '*.*'))
    print(f"\n{style}: {len(files)} 张")
    # 随机抽3张
    import random
    sample = random.sample(files, min(3, len(files)))
    for f in sample:
        img = Image.open(f)
        arr = np.array(img)
        white_pct = (arr > 240).sum() / arr.size * 100
        # 检查来源（云墨济心的是128x128 jpg，字体渲染也是128x128 jpg）
        # 云墨济心特征：白像素比例低，笔画更实
        print(f"  {os.path.basename(f)}: {img.size}, mode={img.mode}, 白像素={white_pct:.1f}%")
