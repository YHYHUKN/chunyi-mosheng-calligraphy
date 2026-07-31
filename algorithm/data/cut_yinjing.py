"""
从褚遂良阴符经长卷中自动切割单字
1. 二值化 + 投影法分割列
2. 列内按连通域分割单字
3. 过滤太小的碎片
4. 保存到 algorithm/data/chushuliang/ 目录
"""
import os
import numpy as np
from PIL import Image, ImageFilter

SRC = r'D:\书法春\褚遂良阴符经原贴.jpg'
OUT_DIR = r'D:\书法春\algorithm\data\chushuliang'
os.makedirs(OUT_DIR, exist_ok=True)

# 1. 加载并预处理
print("加载图片...")
img = Image.open(SRC).convert('L')

# 太大了，先检查是否需要分段处理
w, h = img.size
print(f"原始尺寸: {w}x{h}")

# 二值化（书法: 黑字白底）
threshold = 180
binary = np.array(img) < threshold  # True=墨迹
print(f"墨迹像素占比: {binary.mean()*100:.2f}%")

# 2. 列分割（垂直投影）
col_proj = binary.sum(axis=0)  # 每列的墨迹像素数

# 找列间隙（连续的空白列）
COL_GAP_THRESHOLD = 15  # 连续15列无墨迹视为分隔
in_gap = False
gap_start = 0
col_boundaries = [0]  # 起始列

for x in range(w):
    if col_proj[x] < 5:  # 几乎没有墨迹
        if not in_gap:
            in_gap = True
            gap_start = x
    else:
        if in_gap:
            gap_len = x - gap_start
            if gap_len >= COL_GAP_THRESHOLD:
                mid = (gap_start + x) // 2
                col_boundaries.append(mid)

col_boundaries.append(w)
print(f"检测到 {len(col_boundaries)-1} 列")

# 3. 逐列切字
from scipy import ndimage

char_count = 0
rejected = 0

for col_idx in range(len(col_boundaries) - 1):
    x1 = col_boundaries[col_idx]
    x2 = col_boundaries[col_idx + 1]
    
    col_img = binary[:, x1:x2]
    col_h, col_w = col_img.shape
    
    if col_w < 10 or col_h < 20:
        continue
    
    # 行投影分割
    row_proj = col_img.sum(axis=1)
    
    # 找文字行的上下边界
    row_mask = row_proj > 3
    if not row_mask.any():
        continue
    
    rows_with_ink = np.where(row_mask)[0]
    row_top = max(0, rows_with_ink[0] - 5)
    row_bot = min(col_h, rows_with_ink[-1] + 6)
    
    col_crop = col_img[row_top:row_bot, :]
    
    # 用连通域找单字
    labeled, num_features = ndimage.label(col_crop)
    
    if num_features == 0:
        continue
    
    # 获取每个连通域的边界框
    chars = []
    for i in range(1, num_features + 1):
        ys, xs = np.where(labeled == i)
        if len(ys) < 15 or len(xs) < 8:  # 太小碎片跳过
            rejected += 1
            continue
        area = len(ys)
        chars.append({
            'x1': xs.min(), 'x2': xs.max(),
            'y1': ys.min(), 'y2': ys.max(),
            'area': area
        })
    
    # 按x位置排序
    chars.sort(key=lambda c: c['x1'])
    
    for ci, ch in enumerate(chars):
        # 加padding
        pad = 8
        cy1 = max(0, ch['y1'] + row_top - pad)
        cy2 = min(h, ch['y2'] + row_top + pad + 1)
        cx1 = max(0, x1 + ch['x1'] - pad)
        cx2 = min(w, x1 + ch['x2'] + pad + 1)
        
        cw = cx2 - cx1
        c_h = cy2 - cy1
        
        # 跳过太小的
        if cw < 25 or c_h < 25:
            rejected += 1
            continue
        
        # 跳过太扁或太窄的（可能是碎片）
        aspect = cw / c_h
        if aspect > 3 or aspect < 0.2:
            rejected += 1
            continue
        
        # 切割并resize到128x128
        char_img = Image.open(SRC).convert('L').crop((cx1, cy1, cx2, cy2))
        
        # 保持宽高比resize，白底填充
        target = 128
        ratio = min(target / cw, target / c_h)
        new_w = max(1, int(cw * ratio))
        new_h = max(1, int(c_h * ratio))
        resized = char_img.resize((new_w, new_h), Image.LANCZOS)
        
        # 白底填充到128x128
        canvas = Image.new('L', (target, target), 255)
        paste_x = (target - new_w) // 2
        paste_y = (target - new_h) // 2
        canvas.paste(resized, (paste_x, paste_y))
        
        out_path = os.path.join(OUT_DIR, f'char_{char_count:04d}.png')
        canvas.save(out_path)
        char_count += 1

print(f"\n切割完成!")
print(f"  有效单字: {char_count}")
print(f"  过滤碎片: {rejected}")
print(f"  保存目录: {OUT_DIR}")
