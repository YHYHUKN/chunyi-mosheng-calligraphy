"""对比测试：60 epoch 旧模型 vs 5 epoch 新模型"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r'd:\书法春\algorithm')
sys.path.insert(0, r'd:\书法春')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {device}")

from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator

def test_model(checkpoint_path, name, style_path, char='永'):
    """测试一个模型并保存结果"""
    style_encoder = StyleEncoder(style_dim=128).to(device)
    content_encoder = ContentEncoder(content_dim=256).to(device)
    generator = DualBranchGenerator(content_dim=256, style_dim=128).to(device)
    
    cp = torch.load(checkpoint_path, map_location=device, weights_only=False)
    style_encoder.load_state_dict(cp['style_encoder'])
    content_encoder.load_state_dict(cp['content_encoder'])
    generator.load_state_dict(cp['generator'])
    style_encoder.eval()
    content_encoder.eval()
    generator.eval()
    
    # 风格参考
    style_img = np.array(Image.open(style_path).convert('L'))
    style_tensor = torch.from_numpy(style_img).float().unsqueeze(0).unsqueeze(0)
    style_tensor = (style_tensor / 127.5 - 1.0).to(device)
    
    # 骨架
    size = 128
    pil = Image.new('L', (size, size), 255)
    draw = ImageDraw.Draw(pil)
    try:
        font = ImageFont.truetype(r'C:\Windows\Fonts\STXINGKA.TTF', int(size * 0.7))
    except:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), char, font=font)
    tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]; y = (size - th) // 2 - bbox[1]
    draw.text((x, y), char, fill=0, font=font)
    skeleton_arr = np.array(pil, dtype=np.uint8)
    
    skel_tensor = torch.from_numpy(skeleton_arr).float().unsqueeze(0).unsqueeze(0)
    skel_tensor = (skel_tensor / 127.5 - 1.0).to(device)
    
    with torch.no_grad():
        style_vec = style_encoder(style_tensor)
        content_feat = content_encoder(skel_tensor)
        generated = generator(content_feat, style_vec)
    
    # 后处理 - 多种方式对比
    raw = generated.squeeze().cpu().numpy()
    
    # 方式1：标准映射 [-1,1] → [0,255]
    img1 = ((raw + 1) * 127.5).clip(0, 255).astype(np.uint8)
    
    # 方式2：归一化到 [0,255]
    rmin, rmax = raw.min(), raw.max()
    if rmax > rmin:
        img2 = ((raw - rmin) / (rmax - rmin) * 255).astype(np.uint8)
    else:
        img2 = np.zeros_like(raw, dtype=np.uint8)
    
    # 方式3：sigmoid后映射
    from scipy.special import expit
    img3 = (expit(raw) * 255).astype(np.uint8)
    
    # 方式4：tanh到0-255（训练数据的逆过程）
    img4 = ((raw + 1) / 2 * 255).clip(0, 255).astype(np.uint8)
    
    print(f"\n=== {name} ===")
    print(f"  raw range: [{rmin:.3f}, {rmax:.3f}]")
    print(f"  方式1 (标准): 白{(img1>240).sum()/img1.size*100:.1f}% 黑{(img1<20).sum()/img1.size*100:.1f}%")
    print(f"  方式2 (归一化): 白{(img2>240).sum()/img2.size*100:.1f}% 黑{(img2<20).sum()/img2.size*100:.1f}%")
    print(f"  方式3 (sigmoid): 白{(img3>240).sum()/img3.size*100:.1f}% 黑{(img3<20).sum()/img3.size*100:.1f}%")
    print(f"  方式4 (tanh/2): 白{(img4>240).sum()/img4.size*100:.1f}% 黑{(img4<20).sum()/img4.size*100:.1f}%")
    
    # 保存4种方式对比
    canvas = Image.new('RGB', (128*4 + 30, 128 + 40), (240, 240, 240))
    draw2 = ImageDraw.Draw(canvas)
    draw2.text((10, 5), name, fill=(0,0,0))
    canvas.paste(Image.fromarray(img1), (10, 30))
    canvas.paste(Image.fromarray(img2), (138, 30))
    canvas.paste(Image.fromarray(img3), (266, 30))
    canvas.paste(Image.fromarray(img4), (394, 30))
    draw2.text((10, 160), "标准", fill=(0,0,0))
    draw2.text((138, 160), "归一化", fill=(0,0,0))
    draw2.text((266, 160), "sigmoid", fill=(0,0,0))
    draw2.text((394, 160), "tanh/2", fill=(0,0,0))
    return canvas

# 风格参考图 - 用旧字体渲染数据备份（如果有的话）或当前的
style_path = r'd:\书法春\algorithm\data\米芾\calli_0023.jpg'

# 60 epoch 旧模型
result60 = test_model(
    r'd:\书法春\checkpoints\final\checkpoint_epoch_060.pth',
    '旧模型 60epoch (字体渲染)',
    style_path
)

# 5 epoch 新模型
result5 = test_model(
    r'd:\书法春\checkpoints\checkpoint_epoch_005_best.pth',
    '新模型 5epoch (云墨济心+字体)',
    style_path
)

# 保存对比图
canvas = Image.new('RGB', (542, 128*2 + 100), (255, 255, 255))
canvas.paste(result60, (0, 0))
canvas.paste(result5, (0, 200))

output = r'd:\书法春\debug_model_compare.png'
canvas.save(output)
print(f"\n对比图已保存到: {output}")
