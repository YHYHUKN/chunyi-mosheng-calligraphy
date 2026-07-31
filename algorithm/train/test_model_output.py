"""测试模型输出质量"""
import os, sys
from pathlib import Path

TRAIN_DIR   = Path(__file__).resolve().parent
ALGO_DIR    = TRAIN_DIR.parent
PROJECT_DIR = ALGO_DIR.parent
sys.path.insert(0, str(ALGO_DIR))
os.chdir(str(PROJECT_DIR))

import torch
import numpy as np
from PIL import Image
from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator

cp = torch.load('checkpoints/final/zhao_fast_ep010.pth', map_location='cpu', weights_only=False)
config = cp['config']
print(f'Config: {config}')

generator = DualBranchGenerator(config['style_dim'], config['content_dim'])
generator.load_state_dict(cp['generator'])
generator.eval()

style_encoder = StyleEncoder(config['style_dim'])
style_encoder.load_state_dict(cp['style_encoder'])
style_encoder.eval()

content_encoder = ContentEncoder(config['content_dim'])
content_encoder.load_state_dict(cp['content_encoder'])
content_encoder.eval()

# 用随机噪声测试
style_img = torch.randn(1, 1, 64, 64)
content_img = torch.randn(1, 1, 64, 64)

with torch.no_grad():
    style_feat = style_encoder(style_img)
    content_feat = content_encoder(content_img)
    out = generator(style_feat, content_feat)
    
print(f'Output shape: {out.shape}')
print(f'Output range: [{out.min():.2f}, {out.max():.2f}]')
print(f'Output mean: {out.mean():.2f}')

img = ((out.squeeze().numpy() + 1) * 127.5).clip(0, 255).astype(np.uint8)
Image.fromarray(img).save('checkpoints/test_output.png')
print('Saved to checkpoints/test_output.png')

# 也用训练数据里的真实图片测试
data_dir = ALGO_DIR / 'data' / '赵孟頫'
if data_dir.exists():
    samples = list(data_dir.glob('*.png'))[:3]
    if samples:
        ref = np.array(Image.open(samples[0]).convert('L').resize((64, 64)))
        ref_t = torch.from_numpy(ref).float() / 127.5 - 1
        ref_t = ref_t.unsqueeze(0).unsqueeze(0)
        
        with torch.no_grad():
            s_feat = style_encoder(ref_t)
            c_feat = content_encoder(ref_t)
            out2 = generator(s_feat, c_feat)
        
        print(f'\nReal image test:')
        print(f'Output range: [{out2.min():.2f}, {out2.max():.2f}]')
        print(f'Output mean: {out2.mean():.2f}')
        
        img2 = ((out2.squeeze().numpy() + 1) * 127.5).clip(0, 255).astype(np.uint8)
        Image.fromarray(img2).save('checkpoints/test_output_real.png')
        Image.fromarray(ref).save('checkpoints/test_ref.png')
        print('Saved real image test to checkpoints/test_output_real.png')
    else:
        print('No samples found in data directory')
else:
    print(f'Data directory not found: {data_dir}')
