"""
阴符经切割 v3 - 连通域法
不依赖空白列分割，直接用连通域找每个独立单字
"""
import os, time
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

SRC = r'D:\书法春\褚遂良阴符经原贴.jpg'
OUT_DIR = r'D:\书法春\algorithm\data\chushuliang'
os.makedirs(OUT_DIR, exist_ok=True)

t0 = time.time()
print("加载图片...", flush=True)
img = Image.open(SRC).convert('L')
img_arr = np.array(img)
h, w = img_arr.shape
print(f"尺寸: {w}x{h}", flush=True)

# 二值化
bg = img.filter(ImageFilter.GaussianBlur(radius=40))
bg_arr = np.array(bg)
binary = (bg_arr.astype(int) - img_arr.astype(int)) > 40

# 形态学开运算：去除小噪点
struct = np.ones((3, 3))
binary = ndimage.binary_opening(binary, structure=struct, iterations=2)

# 连通域标记
labeled, num = ndimage.label(binary)
print(f"连通域数量: {num}", flush=True)

# 获取每个连通域的边界框
char_count = 0
skipped = 0
TARGET = 128
chars = []

for i in range(1, num + 1):
    ys, xs = np.where(labeled == i)
    area = len(ys)
    
    # 边界框
    y1, y2 = ys.min(), ys.max() + 1
    x1, x2 = xs.min(), xs.max() + 1
    cw, ch2 = x2 - x1, y2 - y1
    
    # 过滤条件
    if cw < 20 or ch2 < 20 or area < 80:
        skipped += 1
        continue
    if cw / ch2 > 5 or ch2 / cw > 5:
        skipped += 1
        continue
    
    chars.append({
        'x1': x1, 'x2': x2, 'y1': y1, 'y2': y2,
        'area': area, 'w': cw, 'h': ch2
    })

# 按位置排序（从左到右，从上到下）
chars.sort(key=lambda c: (c['y1'] // 100, c['x1']))

# 合并相邻的连通域（同一列中过近的字）
merged = []
used = [False] * len(chars)

for i, c in enumerate(chars):
    if used[i]:
        continue
    box = dict(c)
    for j in range(i + 1, len(chars)):
        if used[j]:
            continue
        d = chars[j]
        # 水平距离很近且垂直重叠
        h_overlap = max(0, min(box['y2'], d['y2']) - max(box['y1'], d['y1']))
        v_overlap = h_overlap / max(box['h'], d['h'])
        h_dist = max(0, d['x1'] - box['x2'])
        
        if v_overlap > 0.3 and h_dist < 15:
            box['x1'] = min(box['x1'], d['x1'])
            box['x2'] = max(box['x2'], d['x2'])
            box['y1'] = min(box['y1'], d['y1'])
            box['y2'] = max(box['y2'], d['y2'])
            box['w'] = box['x2'] - box['x1']
            box['h'] = box['y2'] - box['y1']
            box['area'] += d['area']
            used[j] = True
    merged.append(box)

print(f"合并前: {len(chars)}, 合并后: {len(merged)}", flush=True)

# 保存单字
for ci, ch in enumerate(merged):
    pad = 15
    cy1 = max(0, ch['y1'] - pad)
    cy2 = min(h, ch['y2'] + pad)
    cx1 = max(0, ch['x1'] - pad)
    cx2 = min(w, ch['x2'] + pad)
    
    cw, ch2 = cx2 - cx1, cy2 - cy1
    if cw < 25 or ch2 < 25:
        skipped += 1
        continue
    
    crop = img_arr[cy1:cy2, cx1:cx2]
    crop_img = Image.fromarray(crop)
    
    ratio = min(TARGET / cw, TARGET / ch2)
    nw, nh = max(1, int(cw * ratio)), max(1, int(ch2 * ratio))
    resized = crop_img.resize((nw, nh), Image.LANCZOS)
    
    canvas = Image.new('L', (TARGET, TARGET), 255)
    canvas.paste(resized, ((TARGET - nw) // 2, (TARGET - nh) // 2))
    canvas.save(os.path.join(OUT_DIR, f'char_{ci:04d}.png'))
    char_count += 1

elapsed = time.time() - t0
print(f"\n完成! 耗时 {elapsed:.1f}秒", flush=True)
print(f"有效单字: {char_count}, 过滤: {skipped}", flush=True)
