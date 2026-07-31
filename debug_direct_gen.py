"""独立测试：加载米芾模型直接推理"""
import torch
import torch.nn as nn
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'algorithm'))

from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f'Device: {device}')

# 加载checkpoint
ckpt_path = 'checkpoints/final/mifu_ep030.pth'
ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
config = ckpt.get('config', {})
img_size = config.get('image_size', 128)
style_dim = config.get('style_dim', 128)
content_dim = config.get('content_dim', 256)
print(f'Config: img_size={img_size}, style_dim={style_dim}, content_dim={content_dim}')

# 创建模型
style_enc = StyleEncoder(style_dim=style_dim).to(device)
content_enc = ContentEncoder(content_dim=content_dim).to(device)
generator = DualBranchGenerator(content_dim=content_dim, style_dim=style_dim).to(device)

# 加载权重
style_enc.load_state_dict(ckpt['style_encoder'])
content_enc.load_state_dict(ckpt['content_encoder'])
generator.load_state_dict(ckpt['generator'])
print('Models loaded!')

# 风格编码器：加载一张米芾训练图
import glob
mifu_imgs = glob.glob('algorithm/data/米芾/*.jpg') + glob.glob('algorithm/data/米芾/*.png')
if not mifu_imgs:
    mifu_imgs = glob.glob('algorithm/data/mifu/*.jpg') + glob.glob('algorithm/data/mifu/*.png')
print(f'Found {len(mifu_imgs)} 米芾 images')

if mifu_imgs:
    from PIL import Image as PILImage
    import random
    img_path = random.choice(mifu_imgs)
    print(f'Using style ref: {img_path}')
    img = PILImage.open(img_path).convert('L')
    img = img.resize((img_size, img_size))
    img_arr = np.array(img, dtype=np.float32)
    
    # 显示参考图统计
    print(f'Style ref: min={img_arr.min()}, max={img_arr.max()}, mean={img_arr.mean():.1f}')
    white_pct = (img_arr > 250).sum() / img_arr.size * 100
    print(f'Style ref white%: {white_pct:.1f}%')
    
    # 归一化到 [-1, 1]
    style_tensor = torch.from_numpy(img_arr).unsqueeze(0).unsqueeze(0).to(device)
    style_tensor = (style_tensor / 127.5 - 1.0)
    print(f'Style tensor range: [{style_tensor.min().item():.3f}, {style_tensor.max().item():.3f}]')
    
    # 内容：渲染"永"字骨架
    from PIL import ImageDraw, ImageFont
    font_path = None
    for fp in ['assets/fonts/simkai.ttf', 'assets/fonts/kaiu.ttf', 'C:/Windows/Fonts/simkai.ttf', 'C:/Windows/Fonts/msyh.ttc']:
        if os.path.exists(fp):
            font_path = fp
            break
    pil = PILImage.new('L', (img_size, img_size), 255)
    draw = ImageDraw.Draw(pil)
    try:
        font = ImageFont.truetype(font_path, int(img_size * 0.7)) if font_path else ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    char = '永'
    bbox = draw.textbbox((0, 0), char, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = (img_size - tw) // 2 - bbox[0], (img_size - th) // 2 - bbox[1]
    draw.text((x, y), char, fill=0, font=font)
    skel_arr = np.array(pil, dtype=np.float32)
    
    print(f'Skeleton: min={skel_arr.min()}, max={skel_arr.max()}, mean={skel_arr.mean():.1f}')
    skel_white = (skel_arr > 250).sum() / skel_arr.size * 100
    print(f'Skeleton white%: {skel_white:.1f}%')
    
    skel_tensor = torch.from_numpy(skel_arr).unsqueeze(0).unsqueeze(0).to(device)
    skel_tensor = (skel_tensor / 127.5 - 1.0)
    
    # 推理
    style_enc.eval()
    content_enc.eval()
    generator.eval()
    
    with torch.no_grad():
        style_vec = style_enc(style_tensor)
        print(f'Style vec shape: {style_vec.shape}, range: [{style_vec.min().item():.3f}, {style_vec.max().item():.3f}]')
        
        content_feat = content_enc(skel_tensor)
        print(f'Content feat shape: {content_feat.shape if hasattr(content_feat, "shape") else type(content_feat)}')
        
        result = generator(content_feat, style_vec)
        print(f'Generator output shape: {result.shape}')
        print(f'Generator output range: [{result.min().item():.3f}, {result.max().item():.3f}]')
        print(f'Generator output mean: {result.mean().item():.3f}')
        
        # 后处理
        img_out = result.squeeze().cpu().numpy()
        img_out = ((img_out + 1) * 127.5).clip(0, 255).astype(np.uint8)
        print(f'Output: min={img_out.min()}, max={img_out.max()}, mean={img_out.mean():.1f}')
        out_white = (img_out > 250).sum() / img_out.size * 100
        print(f'Output white%: {out_white:.1f}%')
        
        # 保存
        pil_out = PILImage.fromarray(img_out, mode='L')
        pil_out.save('debug_mifu_direct.png')
        print('Saved debug_mifu_direct.png')
        
        # 也保存风格参考图和骨架图
        PILImage.fromarray(img_arr.astype(np.uint8), mode='L').save('debug_style_ref.png')
        PILImage.fromarray(skel_arr.astype(np.uint8), mode='L').save('debug_skeleton.png')
        print('Saved debug_style_ref.png and debug_skeleton.png')
