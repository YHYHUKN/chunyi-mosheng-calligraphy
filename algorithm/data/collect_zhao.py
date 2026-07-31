# -*- coding: utf-8 -*-
"""
赵孟頫高质量书法数据采集 + 预处理
- 从多个来源搜索白底黑字单字图
- 自动过滤非书法图片（彩色/截图/低质量）
- 自动裁切为单字 + 归一化

用法: python algorithm/data/collect_zhao.py
"""
import os, sys, time, random, hashlib, io, re
from pathlib import Path
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from PIL import Image
import numpy as np

DATA_DIR = Path(__file__).parent / "赵孟頫" / "楷书"
DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 搜索词：专门搜白底黑字单字
QUERIES = [
    "赵孟頫 楷书 单字 白底",
    "赵孟頫 胆巴碑 单字",
    "赵孟頫 妙严寺记 单字",
    "赵孟頫 三门记 单字",
    "赵孟頫 楷书 黑底白字",
    "赵孟頫 楷书 书法字",
    "赵孟頫 楷书 集字",
    "赵孟頫 玄妙观重修三门记 单字",
    "赵孟頫 胆巴碑 集字",
    "赵孟頫 寿春堂记 单字",
    "赵孟頫 楷书 书法 图片",
    "赵孟頫 楷书 作品 高清",
    "zhao mengfu kaishu character",
    "赵孟頫 楷书 贴字",
]


def search_bing(query, count=50):
    """Bing 图片搜索"""
    session = requests.Session()
    session.headers.update(HEADERS)
    urls = []
    try:
        for start in range(1, count, 30):
            url = f"https://www.bing.com/images/search?q={quote(query)}&first={start}&count=30&qft=+filterui:photo-photo"
            resp = session.get(url, timeout=15, verify=False)
            if resp.status_code != 200:
                continue
            found = re.findall(r'murl&quot;:&quot;(https?://[^&]+)&quot;', resp.text)
            if not found:
                found = re.findall(r'"murl":"(https?://[^"]+)"', resp.text)
            urls.extend(found)
            time.sleep(0.5)
    except:
        pass
    return list(set(urls))


def search_google(query, count=30):
    """Google 图片搜索"""
    session = requests.Session()
    session.headers.update(HEADERS)
    urls = []
    try:
        url = f"https://www.google.com/search?q={quote(query)}&tbm=isch&num={count}"
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return urls
        # 提取图片 URL
        found = re.findall(r'"ou":"(https?://[^"]+)"', resp.text)
        urls.extend(found)
    except:
        pass
    return list(set(urls))


def download_image(url, timeout=10):
    """下载图片返回 bytes"""
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        resp = session.get(url, stream=True, timeout=timeout)
        if resp.status_code != 200:
            return None
        content = resp.content
        if len(content) < 3000:
            return None
        return content
    except:
        return None


def is_calligraphy_quality(img: Image.Image) -> bool:
    """
    判断图片是否为高质量的书法单字
    返回 True = 合格
    """
    # 转灰度
    gray = np.array(img.convert("L"))

    # 1. 尺寸检查：太小说明是 icon/logo
    w, h = img.size
    if w < 64 or h < 64:
        return False

    # 2. 颜色检查：书法应该是接近灰度图
    rgb = np.array(img.convert("RGB"))
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    color_var = (np.std(r - g) + np.std(g - b) + np.std(r - b)) / 3.0
    # 彩色图片（网页截图等）色差大
    if color_var > 25:
        return False

    # 3. 对比度检查：笔画和背景要有足够对比
    # 白底黑字：大部分像素应该偏白或偏黑
    bright_pct = (gray > 200).sum() / gray.size  # 白色像素占比
    dark_pct = (gray < 60).sum() / gray.size     # 黑色像素占比

    # 理想情况：白底黑字 = bright_pct > 40% 且有 dark_pct > 2%
    # 或黑底白字 = dark_pct > 40% 且有 bright_pct > 2%
    is_white_bg = bright_pct > 0.35 and dark_pct > 0.02
    is_black_bg = dark_pct > 0.35 and bright_pct > 0.02

    if not (is_white_bg or is_black_bg):
        return False

    # 4. 内容检查：不能太均匀（纯色/渐变等）
    hist, _ = np.histogram(gray, bins=50, range=(0, 256))
    hist = hist / hist.sum()
    # 有效的书法图应该有明显的双峰（背景+笔画）
    nonzero_bins = (hist > 0.005).sum()
    if nonzero_bins < 5:
        return False

    # 5. 宽高比检查：单字应该接近正方形或略长
    aspect = w / h
    if aspect < 0.3 or aspect > 3.0:
        return False

    return True


def preprocess_single_char(img: Image.Image, target_size=128) -> Image.Image | None:
    """
    预处理为标准单字图：
    1. 转灰度
    2. 二值化
    3. 找到文字区域并裁切
    4. 居中到 target_size x target_size 白底画布
    """
    gray = np.array(img.convert("L"))

    # 判断是白底还是黑底
    bright_pct = (gray > 200).sum() / gray.size
    if bright_pct > 0.5:
        # 白底黑字 - 直接用
        binary = cv2_threshold_inv(gray)
        canvas_color = 255
    else:
        # 黑底白字 - 反转
        gray = 255 - gray
        binary = cv2_threshold_inv(gray)
        canvas_color = 255

    # 找文字区域
    coords = np.column_stack(np.where(binary > 128))
    if len(coords) == 0:
        return None

    y_min, x_min = coords.min(axis=0)
    y_max, x_max = coords.max(axis=0)

    # 加一点 padding
    pad = max(x_max - x_min, y_max - y_min) // 8
    x_min = max(0, x_min - pad)
    y_min = max(0, y_min - pad)
    x_max = min(gray.shape[1], x_max + pad)
    y_max = min(gray.shape[0], y_max + pad)

    # 裁切
    cropped = gray[y_min:y_max, x_min:x_max]
    ch, cw = cropped.shape

    if cw < 10 or ch < 10:
        return None

    # 缩放到画布
    canvas = np.full((target_size, target_size), canvas_color, dtype=np.uint8)
    scale = min((target_size - 10) / ch, (target_size - 10) / cw)
    new_h, new_w = int(ch * scale), int(cw * scale)
    if new_h < 4 or new_w < 4:
        return None

    # 简单缩放（不用 cv2，避免依赖）
    pil_crop = Image.fromarray(cropped)
    pil_resize = pil_crop.resize((new_w, new_h), Image.LANCZOS)
    resized = np.array(pil_resize)

    # 居中
    ox = (target_size - new_w) // 2
    oy = (target_size - new_h) // 2
    canvas[oy:oy+new_h, ox:ox+new_w] = resized

    return Image.fromarray(canvas)


def cv2_threshold_inv(gray):
    """简单二值化（不依赖 cv2）"""
    # Otsu 近似：用中间值
    median = np.median(gray)
    _, binary = np.where(gray > median, 0, 255).astype(np.uint8), None
    # 更好的方式：自适应阈值
    # 用 PIL 的方式
    from PIL import ImageFilter
    pil = Image.fromarray(gray)
    pil = pil.filter(ImageFilter.MedianFilter(size=3))
    arr = np.array(pil)
    # 大津法近似
    threshold = arr.mean() - arr.std() * 0.3
    binary = np.where(arr > threshold, 0, 255).astype(np.uint8)
    return binary


def main():
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    TARGET = 200  # 目标采集数量
    existing = len(list(DATA_DIR.glob("*.jpg")))
    need = TARGET - existing

    if need <= 0:
        print(f"已有 {existing} 张，够用了")
        return

    print("=" * 60)
    print(f"  赵孟頫楷书 - 高质量单字采集")
    print(f"  目标: {TARGET} 张 (已有 {existing}，还需 {need})")
    print("=" * 60)

    # ---- 第1步：搜索图片URL ----
    print("\n[1/3] 搜索图片URL...")
    all_urls = set()
    for i, query in enumerate(QUERIES):
        if len(all_urls) >= need * 3:
            break
        print(f"  [{i+1}/{len(QUERIES)}] {query}")
        # Bing
        urls = search_bing(query, count=50)
        all_urls.update(urls)
        # Google (少量)
        if i < 5:
            gurls = search_google(query, count=20)
            all_urls.update(gurls)
        print(f"    累计 {len(all_urls)} 个URL")
        time.sleep(random.uniform(1.0, 2.5))

    all_urls = list(all_urls)
    random.shuffle(all_urls)
    print(f"  共 {len(all_urls)} 个候选URL")

    # ---- 第2步：下载 + 质量过滤 + 预处理 ----
    print(f"\n[2/3] 下载并过滤 (目标 {need} 张合格)...")
    downloaded = 0
    filtered_out = 0
    saved = 0

    for url in all_urls:
        if saved >= need:
            break

        file_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        save_path = DATA_DIR / f"{file_hash}.jpg"
        if save_path.exists():
            saved += 1
            continue

        content = download_image(url)
        if content is None:
            continue

        downloaded += 1

        try:
            img = Image.open(io.BytesIO(content))
            img.load()
        except:
            continue

        # 质量检查
        if not is_calligraphy_quality(img):
            filtered_out += 1
            continue

        # 预处理为标准单字
        processed = preprocess_single_char(img, target_size=128)
        if processed is None:
            filtered_out += 1
            continue

        # 保存
        processed.save(save_path, quality=95)
        saved += 1
        if saved % 20 == 0:
            print(f"    已保存 {saved}/{need} (下载 {downloaded}, 过滤 {filtered_out})")

        time.sleep(0.2)

    # ---- 第3步：统计 ----
    final_count = len(list(DATA_DIR.glob("*.jpg")))
    print(f"\n[3/3] 完成!")
    print(f"  下载: {downloaded}, 过滤: {filtered_out}, 保存: {saved}")
    print(f"  最终: {final_count} 张高质量单字")

    # 抽样展示质量
    print(f"\n  质量抽检 (前5张):")
    for f in sorted(DATA_DIR.glob("*.jpg"))[:5]:
        im = np.array(Image.open(f).convert("L"))
        bright = (im > 200).sum() / im.size
        dark = (im < 60).sum() / im.size
        print(f"    {f.name}: 白{bright:.0%} 黑{dark:.0%} 尺寸{Image.open(f).size}")


if __name__ == "__main__":
    main()
