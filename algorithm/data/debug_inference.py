"""直接测试模型推理，打印中间结果诊断问题"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import torch
import numpy as np
from PIL import Image

sys.path.insert(0, r'd:\书法春\algorithm')
sys.path.insert(0, r'd:\书法春')

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {device}")

# 加载模型
from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator

style_encoder = StyleEncoder(style_dim=128).to(device)
content_encoder = ContentEncoder(content_dim=256).to(device)
generator = DualBranchGenerator(content_dim=256, style_dim=128).to(device)

cp = torch.load(r'd:\书法春\checkpoints\final\checkpoint_epoch_060.pth', 
                map_location=device, weights_only=False)
style_encoder.load_state_dict(cp['style_encoder'])
content_encoder.load_state_dict(cp['content_encoder'])
generator.load_state_dict(cp['generator'])
style_encoder.eval()
content_encoder.eval()
generator.eval()
print("模型加载成功")

# 风格参考图 - 从当前训练数据（云墨济心）取一张米芾
style_path = r'd:\书法春\algorithm\data\米芾\calli_0023.jpg'
style_img = np.array(Image.open(style_path).convert('L'))
print(f"风格参考图: {style_img.shape}, dtype={style_img.dtype}, range=[{style_img.min()}, {style_img.max()}]")
print(f"  白像素比例: {(style_img > 240).sum() / style_img.size * 100:.1f}%")
print(f"  黑像素比例: {(style_img < 20).sum() / style_img.size * 100:.1f}%")

# 预处理风格图
style_tensor = torch.from_numpy(style_img).float().unsqueeze(0).unsqueeze(0)
style_tensor = (style_tensor / 127.5 - 1.0).to(device)
print(f"\n风格tensor: shape={style_tensor.shape}, range=[{style_tensor.min():.3f}, {style_tensor.max():.3f}]")

# 提取风格向量
with torch.no_grad():
    style_vec = style_encoder(style_tensor)
print(f"风格向量: shape={style_vec.shape}, range=[{style_vec.min():.3f}, {style_vec.max():.3f}], mean={style_vec.mean():.4f}")

# 内容骨架 - 渲染一个"永"字
from PIL import ImageDraw, ImageFont
size = 128
pil = Image.new('L', (size, size), 255)
draw = ImageDraw.Draw(pil)
try:
    font = ImageFont.truetype(r'C:\Windows\Fonts\STXINGKA.TTF', int(size * 0.7))
except:
    font = ImageFont.load_default()
bbox = draw.textbbox((0, 0), '永', font=font)
tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
x = (size - tw) // 2 - bbox[0]; y = (size - th) // 2 - bbox[1]
draw.text((x, y), '永', fill=0, font=font)
skeleton_arr = np.array(pil, dtype=np.uint8)
print(f"\n骨架图: shape={skeleton_arr.shape}, range=[{skeleton_arr.min()}, {skeleton_arr.max()}]")
print(f"  白像素比例: {(skeleton_arr > 240).sum() / skeleton_arr.size * 100:.1f}%")
print(f"  黑像素比例: {(skeleton_arr < 20).sum() / skeleton_arr.size * 100:.1f}%")

skel_tensor = torch.from_numpy(skeleton_arr).float().unsqueeze(0).unsqueeze(0)
skel_tensor = (skel_tensor / 127.5 - 1.0).to(device)
print(f"骨架tensor: range=[{skel_tensor.min():.3f}, {skel_tensor.max():.3f}]")

# 提取内容特征
with torch.no_grad():
    content_feat = content_encoder(skel_tensor)
print(f"内容特征: shape={content_feat.shape}, range=[{content_feat.min():.3f}, {content_feat.max():.3f}]")

# 生成
with torch.no_grad():
    generated = generator(content_feat, style_vec)
print(f"\n生成结果: shape={generated.shape}, range=[{generated.min():.3f}, {generated.max():.3f}]")

# 后处理
img = generated.squeeze().cpu().numpy()
print(f"后处理前: range=[{img.min():.3f}, {img.max():.3f}]")
img = ((img + 1) * 127.5).clip(0, 255).astype(np.uint8)
print(f"后处理后: range=[{img.min()}, {img.max()}]")
print(f"  白像素比例: {(img > 240).sum() / img.size * 100:.1f}%")
print(f"  黑像素比例: {(img < 20).sum() / img.size * 100:.1f}%")

# 保存结果
Image.fromarray(img).save(r'd:\书法春\debug_gen_60epoch.png')
print(f"\n生成图已保存到 d:\\书法春\\debug_gen_60epoch.png")
