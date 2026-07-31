# -*- coding: utf-8 -*-
"""
整合云墨济心真实书法数据到训练目录
- 将256×256 PNG缩放到128×128
- 云墨济心数据 + 现有字体渲染数据合并
- 乙瑛碑目录用吴让之-隶数据填充
"""
import sys, os, shutil
from pathlib import Path
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

CALLI_TONGJI = Path(r"D:\书法春\书法字库\Calli-Tongji\Calli-Tongji")
DATA_DIR = Path(r"D:\书法春\algorithm\data")
TARGET_SIZE = 128

# 云墨济心目录名 → 训练目录名 映射
# 乙瑛碑保持目录名不变，但数据来源改为吴让之-隶
CALLI_MAP = {
    "米芾-行":  "米芾",
    "赵孟頫-楷": "赵孟頫",
    "褚遂良-楷": "褚遂良",
    "吴让之-隶": "乙瑛碑",   # 吴让之替换乙瑛碑
    "邓石如-篆": "邓石如",
    "怀素-草":  "怀素",
}


def process_image(src_path: Path, dst_path: Path, target_size: int = TARGET_SIZE):
    """读取256×256 PNG → 缩放到128×128 → 保存为JPG"""
    try:
        img = Image.open(src_path).convert("L")  # 灰度
        
        # 缩放到目标尺寸，使用LANCZOS高质量缩放
        if img.size != (target_size, target_size):
            img = img.resize((target_size, target_size), Image.LANCZOS)
        
        # 保存为JPG
        img.save(dst_path, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"    ⚠ 处理失败 {src_path.name}: {e}")
        return False


def main():
    print("=" * 60)
    print("  云墨济心数据整合工具")
    print("=" * 60)
    
    # 备份原有数据
    backup_dir = DATA_DIR / "_backup_font_render"
    if not backup_dir.exists():
        print("\n📦 备份原有字体渲染数据...")
        for style_name in CALLI_MAP.values():
            src = DATA_DIR / style_name
            if src.exists():
                dst = backup_dir / style_name
                shutil.copytree(src, dst)
                print(f"   已备份: {style_name}/")
        print(f"   备份位置: {backup_dir}")
    else:
        print(f"\n📦 备份已存在，跳过 ({backup_dir})")
    
    # 整合云墨济心数据
    total_added = 0
    print("\n🔄 开始整合云墨济心数据...")
    
    for calli_dir, train_dir in CALLI_MAP.items():
        src_dir = CALLI_TONGJI / calli_dir
        dst_dir = DATA_DIR / train_dir
        
        if not src_dir.exists():
            print(f"\n❌ 源目录不存在: {calli_dir}")
            continue
        
        # 获取源PNG列表
        src_pngs = sorted(src_dir.glob("*.png"))
        if not src_pngs:
            print(f"\n❌ 没有图片: {calli_dir}")
            continue
        
        # 获取目标目录已有文件
        dst_dir.mkdir(parents=True, exist_ok=True)
        existing = set(dst_dir.glob("*.jpg")) | set(dst_dir.glob("*.png"))
        existing_names = {f.stem for f in existing}
        
        added = 0
        skipped = 0
        
        print(f"\n{'─' * 50}")
        print(f"[{calli_dir}] → [{train_dir}/]")
        print(f"   源: {len(src_pngs)} 张PNG")
        print(f"   已有: {len(existing)} 张")
        
        for i, src_png in enumerate(src_pngs):
            dst_name = f"calli_{i:04d}.jpg"
            dst_path = dst_dir / dst_name
            
            if process_image(src_png, dst_path):
                added += 1
        
        total_files = len(list(dst_dir.glob("*.jpg"))) + len(list(dst_dir.glob("*.png")))
        print(f"   ✅ 新增: {added} 张, 总计: {total_files} 张")
        total_added += added
    
    # 质量抽检
    print(f"\n{'=' * 60}")
    print(f"📊 整合完成! 新增 {total_added} 张真实书法数据")
    print(f"\n📋 各风格最终数据量:")
    
    for style_name in CALLI_MAP.values():
        style_dir = DATA_DIR / style_name
        if not style_dir.exists():
            print(f"   ❌ {style_name}: 目录不存在")
            continue
        
        total = 0
        calli_count = 0
        font_count = 0
        
        for f in style_dir.rglob("*.jpg"):
            total += 1
            if f.stem.startswith("calli_"):
                calli_count += 1
            else:
                font_count += 1
        for f in style_dir.rglob("*.png"):
            total += 1
            if f.stem.startswith("calli_"):
                calli_count += 1
            else:
                font_count += 1
        
        print(f"   {style_name}: {total}张 (真实书法{calli_count} + 字体渲染{font_count})")
    
    # 抽检几张质量
    print(f"\n🔬 质量抽检:")
    for style_name in CALLI_MAP.values():
        style_dir = DATA_DIR / style_name
        calli_files = sorted([f for f in style_dir.rglob("*.jpg") if f.stem.startswith("calli_")])
        if calli_files:
            sample = calli_files[0]
            img = np.array(Image.open(sample).convert("L"))
            white = (img > 200).sum() / img.size
            dark = (img < 60).sum() / img.size
            print(f"   {style_name}/{sample.name}: {img.shape}, 白{white:.0%} 黑{dark:.0%}")
    
    print(f"\n{'=' * 60}")
    print(f"✅ 数据整合完成! 可以重新训练模型了")
    print(f"   备份位置: {backup_dir}")
    print(f"   训练数据: {DATA_DIR}")


if __name__ == "__main__":
    main()
