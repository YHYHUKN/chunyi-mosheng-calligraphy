# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'algorithm')
from pathlib import Path

print('=== 检查数据目录 ===')
data_root = Path('algorithm/data')
for name in ['米芾','赵孟頫','褚遂良','乙瑛碑','邓石如','怀素']:
    base = data_root / name
    jpgs = list(base.rglob('*.jpg'))
    pngs = list(base.rglob('*.png'))
    print(f'  {name}: {len(jpgs)} jpg + {len(pngs)} png = {len(jpgs)+len(pngs)}')

cache_dir = data_root / '.skeleton_cache'
if cache_dir.exists():
    cached = list(cache_dir.glob('*.npz'))
    print(f'\n骨架缓存: {len(cached)} 个文件')
else:
    print('\n骨架缓存: 目录不存在')

ckpt_dir = Path('checkpoints')
ckpts = list(ckpt_dir.glob('*.pth')) + list(ckpt_dir.glob('*.json'))
print(f'Checkpoint目录: {len(ckpts)} 个文件')

print(f'\n=== 检查CUDA ===')
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
else:
    print('WARNING: CUDA不可用，将使用CPU训练（很慢）')
