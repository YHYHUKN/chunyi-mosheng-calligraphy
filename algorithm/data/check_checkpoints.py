"""检查所有checkpoint的配置，对比是哪次训练"""
import torch, sys, os
sys.stdout.reconfigure(encoding='utf-8')

ckpt_dir = r'd:\书法春\checkpoints'

# 检查根目录下的 .pth 文件
for f in sorted(os.listdir(ckpt_dir)):
    fp = os.path.join(ckpt_dir, f)
    if f.endswith('.pth'):
        print(f'=== {f} ===')
        cp = torch.load(fp, map_location='cpu', weights_only=False)
        print(f'  epoch: {cp.get("epoch", "?")}')
        cfg = cp.get('config', {})
        print(f'  data_root: {cfg.get("data_root", "?")}')
        print(f'  batch_size: {cfg.get("batch_size", "?")}')
        print(f'  num_epochs: {cfg.get("num_epochs", "?")}')
        print(f'  aug_factor: {cfg.get("aug_factor", "?")}')
        sm = cp.get('style_map', {})
        print(f'  style_map: {sm}')
        print()

# 检查 final 目录
final_dir = os.path.join(ckpt_dir, 'final')
if os.path.exists(final_dir):
    for f in sorted(os.listdir(final_dir)):
        if f.endswith('.pth'):
            print(f'=== final/{f} ===')
            cp = torch.load(os.path.join(final_dir, f), map_location='cpu', weights_only=False)
            print(f'  epoch: {cp.get("epoch", "?")}')
            cfg = cp.get('config', {})
            print(f'  data_root: {cfg.get("data_root", "?")}')
            print(f'  batch_size: {cfg.get("batch_size", "?")}')
            print(f'  num_epochs: {cfg.get("num_epochs", "?")}')
            print(f'  aug_factor: {cfg.get("aug_factor", "?")}')
            sm = cp.get('style_map', {})
            print(f'  style_map: {sm}')
            print()
