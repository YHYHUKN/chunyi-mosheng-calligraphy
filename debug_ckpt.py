import torch, os, sys
sys.stdout.reconfigure(encoding='utf-8')
final_dir = 'checkpoints/final'
for f in os.listdir(final_dir):
    if f.endswith('.pth'):
        ckpt = torch.load(os.path.join(final_dir, f), map_location='cpu', weights_only=False)
        gw = ckpt['generator']['style_fc.weight']
        print(f'{f}: style_fc.weight = {tuple(gw.shape)}')
        sb = int((gw.shape[0]/64)**0.5)
        print(f'  spatial_base={sb}, image_size={sb*16}')
        cfg = ckpt.get('config', {})
        print(f'  config image_size={cfg.get("image_size", "N/A")}')
