# -*- coding: utf-8 -*-
"""
书法数据自动采集脚本 v2
通过 Bing 图片搜索批量下载名家字帖图片

支持风格：米芾行书、赵孟頫楷书、褚遂良楷书、乙瑛碑隶书、邓石如篆书、怀素草书

用法：
  python collect_data.py                    # 采集所有风格
  python collect_data.py --styles 米芾 赵孟頫 # 只采集指定风格
  python collect_data.py --min-count 50     # 每种风格至少50张
  python collect_data.py --clean            # 只清理无效图片
"""

import os
import sys
import time
import random
import hashlib
import argparse
import re
from pathlib import Path
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from PIL import Image
import io

# ============ 配置 ============

OUTPUT_DIR = Path(__file__).parent  # algorithm/data/

# 常用汉字（用于构建搜索词）
COMMON_CHARS = list(
    "天地人和风花雪月山水云龙凤鹤松竹梅兰菊荷柳桃李杏杨"
    "春夏秋冬东西南北金木火土日月星辰江河海湖溪泉潭瀑"
    "仁义礼智信忠孝廉耻勇毅刚正和平安宁静远深高明通达"
    "文章诗词书画墨笔砚纸色青红白黑紫碧苍翠丹朱金玉"
    "上下左右前后大小多少长短宽窄远近高低深浅轻重缓急"
    "一二三四五六七八九十百千万亿"
    "王侯将相国城门道路桥船车马鸟兽鱼虫"
    "福禄寿喜吉祥如意瑞泰康宁富贵荣华"
    "道德经书礼乐春秋永平年中正大光明元亨利贞乾坤"
    "心性情怀志意思念感悟知道理法术势"
    "清浊浓淡干湿粗细刚柔方圆曲直"
    "动静行止起落收放开合张弛进退"
    "飞舞飘洒挥洒涂抹勾勒点画"
    "生老病死苦乐悲欢离合"
)

# 风格定义 - 每种风格多个搜索词组合
STYLES = {
    "米芾": {
        "script": "行书",
        "queries": [
            "米芾 蜀素帖 单字",
            "米芾 苕溪诗帖 单字",
            "米芾 行书 字帖",
            "米芾 珊瑚帖",
            "米芾 研山铭 书法",
            "米芾 行书 高清",
        ],
    },
    "赵孟頫": {
        "script": "楷书",
        "queries": [
            "赵孟頫 胆巴碑 单字",
            "赵孟頫 妙严寺记 单字",
            "赵孟頫 三门记 单字",
            "赵孟頫 楷书 字帖",
            "赵孟頫 洛神赋 书法",
            "赵孟頫 楷书 高清",
        ],
    },
    "褚遂良": {
        "script": "楷书",
        "queries": [
            "褚遂良 雁塔圣教序 单字",
            "褚遂良 阴符经 单字",
            "褚遂良 孟法师碑 单字",
            "褚遂良 楷书 字帖",
            "褚遂良 伊阙佛龛碑",
            "褚遂良 楷书 高清",
        ],
    },
    "乙瑛碑": {
        "script": "隶书",
        "queries": [
            "乙瑛碑 单字",
            "乙瑛碑 隶书 字帖",
            "乙瑛碑 高清 原石",
            "乙瑛碑 全文 隶书",
            "汉隶 乙瑛碑",
        ],
    },
    "邓石如": {
        "script": "篆书",
        "queries": [
            "邓石如 篆书 单字",
            "邓石如 白氏草堂记",
            "邓石如 篆书 千字文",
            "邓石如 篆书 字帖",
            "邓石如 弟子职 篆书",
        ],
    },
    "怀素": {
        "script": "草书",
        "queries": [
            "怀素 自叙帖 单字",
            "怀素 苦笋帖",
            "怀素 小草千字文",
            "怀素 草书 字帖",
            "怀素 论书帖",
            "怀素 草书 高清",
        ],
    },
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}


class CalligraphyCollector:
    """通过 Bing 图片搜索采集书法字帖"""

    def __init__(self, output_dir: Path, min_count: int = 100, delay: float = 0.3):
        self.output_dir = output_dir
        self.min_count = min_count
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.timeout = 15

        self.stats = {"success": 0, "skip": 0, "fail": 0}

    def _download_image(self, url: str, save_path: Path, min_size=2000) -> bool:
        """下载单张图片并校验"""
        for attempt in range(3):
            try:
                resp = self.session.get(url, stream=True, timeout=15)
                if resp.status_code != 200:
                    time.sleep(self.delay)
                    continue

                content = resp.content
                if len(content) < min_size:
                    self.stats["skip"] += 1
                    return False

                # 校验图片格式
                try:
                    img = Image.open(io.BytesIO(content))
                    img.load()
                    w, h = img.size
                    if w < 32 or h < 32:
                        self.stats["skip"] += 1
                        return False
                    # 如果太大（整幅作品），跳过
                    if w > 4096 or h > 4096:
                        self.stats["skip"] += 1
                        return False
                except Exception:
                    self.stats["skip"] += 1
                    return False

                save_path.write_bytes(content)
                self.stats["success"] += 1
                return True

            except Exception:
                if attempt == 2:
                    self.stats["fail"] += 1
                time.sleep(self.delay * (attempt + 1))

        return False

    def _bing_image_search(self, query: str, count: int = 35) -> list:
        """通过 Bing 图片搜索获取图片 URL"""
        try:
            url = f"https://www.bing.com/images/search?q={quote(query)}&first=1&count={count}&qft=+filterui:photo-photo"
            resp = self.session.get(url, timeout=15, verify=False)
            if resp.status_code != 200:
                return []

            # 提取 murl（中等尺寸原图）
            img_urls = re.findall(r'murl&quot;:&quot;(https?://[^&]+)&quot;', resp.text)
            if not img_urls:
                img_urls = re.findall(r'"murl":"(https?://[^"]+)"', resp.text)
            if not img_urls:
                img_urls = re.findall(r'(https?://[^"\s]+?\.(?:jpg|jpeg|png))', resp.text)

            return [u for u in img_urls if u]

        except Exception:
            return []

    def collect_style(self, name: str, config: dict) -> int:
        """采集某一种风格的书法图片"""
        script = config["script"]
        queries = config["queries"]

        output_dir = self.output_dir / name / script
        output_dir.mkdir(parents=True, exist_ok=True)

        # 统计已有文件
        existing = len(list(output_dir.glob("*.jpg"))) + len(list(output_dir.glob("*.png")))
        if existing >= self.min_count:
            print(f"  ✅ [{name}] 已有 {existing} 张，跳过")
            return existing

        need = self.min_count - existing
        total_new = 0

        for query in queries:
            if total_new >= need:
                break

            print(f"  🔍 搜索: {query}")
            img_urls = self._bing_image_search(query, count=35)
            print(f"     找到 {len(img_urls)} 张候选")

            # 随机打乱
            random.shuffle(img_urls)

            for img_url in img_urls:
                if total_new >= need:
                    break

                file_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
                save_path = output_dir / f"{file_hash}.jpg"

                if save_path.exists():
                    continue

                if self._download_image(img_url, save_path):
                    total_new += 1
                    print(f"     ✅ 下载成功 ({total_new}/{need})")
                else:
                    print(f"     ⏭️ 跳过 ({total_new}/{need})")

                time.sleep(self.delay)

            time.sleep(random.uniform(1.5, 3.0))

        final = existing + total_new
        print(f"  📊 [{name}] 新增 {total_new} 张，总计 {final} 张")
        return final

    def collect_all(self, style_names: list = None):
        """采集所有风格"""
        if style_names is None:
            style_names = list(STYLES.keys())

        print("=" * 60)
        print("  🎨 书法数据自动采集 (Bing 图片搜索)")
        print(f"  📁 输出目录: {self.output_dir}")
        print(f"  🎯 目标: 每种风格至少 {self.min_count} 张")
        print(f"  📋 采集风格: {', '.join(style_names)}")
        print("=" * 60)

        start_time = time.time()
        results = {}

        for name in style_names:
            if name not in STYLES:
                print(f"\n⚠️  未知风格: {name}, 跳过")
                continue

            config = STYLES[name]
            print(f"\n{'─' * 50}")
            print(f"📌 [{name}] {config['script']}")
            print(f"{'─' * 50}")

            try:
                count = self.collect_style(name, config)
                results[name] = count
            except Exception as e:
                print(f"  ❌ [{name}] 失败: {e}")
                results[name] = 0

        # 最终统计
        elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"  ✅ 采集完成！用时 {elapsed:.1f} 秒")
        print(f"{'=' * 60}")

        total_all = 0
        for name, count in results.items():
            status = "✅" if count >= self.min_count else "⚠️"
            print(f"  {status} {name}: {count} 张")
            total_all += count

        print(f"\n  📊 总计: {total_all} 张图片")
        print(f"  📊 下载成功: {self.stats['success']}, 跳过: {self.stats['skip']}, 失败: {self.stats['fail']}")

        return results


def clean_invalid_images(data_dir: Path):
    """清理无效图片"""
    total_checked = 0
    total_removed = 0

    print("\n🧹 清理无效图片...")

    for ext in ("*.jpg", "*.png", "*.jpeg", "*.webp"):
        for img_path in list(data_dir.rglob(ext)):
            total_checked += 1
            try:
                with Image.open(img_path) as img:
                    w, h = img.size
                    if w < 32 or h < 32:
                        img_path.unlink()
                        total_removed += 1
                        continue
                    img.load()
            except Exception:
                img_path.unlink()
                total_removed += 1

    print(f"  检查 {total_checked} 张，删除 {total_removed} 张无效图片")


def split_large_images(data_dir: Path):
    """将整幅作品大图分割成单字（简单版：直接缩放保存）"""
    print("\n✂️ 处理大图...")

    for style_dir in data_dir.iterdir():
        if not style_dir.is_dir():
            continue
        for script_dir in style_dir.iterdir():
            if not script_dir.is_dir():
                continue
            for ext in ("*.jpg", "*.png"):
                for img_path in list(script_dir.glob(ext)):
                    try:
                        with Image.open(img_path) as img:
                            w, h = img.size
                            # 如果图片太大（可能是整幅作品），缩放到单字大小
                            max_dim = 512
                            if w > max_dim or h > max_dim:
                                # 等比缩放
                                ratio = min(max_dim / w, max_dim / h)
                                new_w = int(w * ratio)
                                new_h = int(h * ratio)
                                img_resized = img.resize((new_w, new_h), Image.LANCZOS)
                                img_resized.save(img_path)
                    except Exception:
                        pass

    print("  处理完成")


def main():
    # 修复 Windows 控制台编码
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description="书法数据自动采集 (Bing)")
    parser.add_argument("--styles", nargs="+", default=None,
                        help="指定采集风格，如: --styles 米芾 赵孟頫")
    parser.add_argument("--min-count", type=int, default=100,
                        help="每种风格最少图片数 (默认: 100)")
    parser.add_argument("--output", type=str, default=None,
                        help="输出目录 (默认: algorithm/data/)")
    parser.add_argument("--clean", action="store_true",
                        help="只清理无效图片，不采集")
    parser.add_argument("--delay", type=float, default=0.3,
                        help="请求间隔秒数 (默认: 0.3)")

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.clean:
        clean_invalid_images(output_dir)
        return

    collector = CalligraphyCollector(output_dir, min_count=args.min_count, delay=args.delay)
    results = collector.collect_all(args.styles)

    # 采集完成后清理和整理
    if sum(results.values()) > 0:
        clean_invalid_images(output_dir)
        split_large_images(output_dir)

        # 打印目录结构
        print(f"\n📁 最终目录结构:")
        for style_dir in sorted(output_dir.iterdir()):
            if not style_dir.is_dir():
                continue
            for script_dir in sorted(style_dir.iterdir()):
                if not script_dir.is_dir():
                    continue
                files = list(script_dir.glob("*.jpg")) + list(script_dir.glob("*.png"))
                print(f"  {style_dir.name}/{script_dir.name}: {len(files)} 张")


if __name__ == "__main__":
    main()
