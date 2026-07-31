"""检查生成器输出尺寸 vs 训练数据尺寸"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import torch
sys.path.insert(0, r'd:\书法春\algorithm')
from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator

device = 'cpu'
style_dim = 128
content_dim = 256

style_enc = StyleEncoder(style_dim=style_dim)
content_enc = ContentEncoder(content_dim=content_dim)
generator = DualBranchGenerator(content_dim=content_dim, style_dim=style_dim)

# 模拟训练数据：128x128 灰度图
img = torch.randn(2, 1, 128, 128)   # 2 batch, 1 channel, 128x128
skel = torch.randn(2, 1, 128, 128)

sv = style_enc(img)
cf = content_enc(skel)

print(f"输入图片: {img.shape}")
print(f"风格向量: {sv.shape}")
print(f"骨架特征: {cf.shape}")

out = generator(cf, sv)
print(f"生成器输出: {out.shape}")
print(f"\n⚠️ 训练数据是 128x128，生成器输出是 {out.shape[2]}x{out.shape[3]}")
if out.shape[2] != 128 or out.shape[3] != 128:
    print("❌ 尺寸不匹配！生成器输出是256x256，但训练数据/target是128x128")
    print("   这意味着生成器试图生成256x256，但target是128x128")
    print("   所有重建损失都可能在比较不同尺寸的图，导致训练失败！")
else:
    print("✅ 尺寸匹配")

# 检查生成器内部各层尺寸
print("\n--- 生成器内部尺寸追踪 ---")
B = 2
x = cf
print(f"内容输入: {x.shape}")
for i, block in enumerate(generator.content_up):
    x = block(x, sv)
    print(f"  content_up[{i}]: {x.shape}")

style_feat = generator.style_fc(sv)
style_feat = style_feat.view(B, 64, 16, 16)
print(f"\n风格展开: {style_feat.shape}")
for i, up in enumerate(generator.style_up):
    style_feat = up(style_feat)
    print(f"  style_up[{i}]: {style_feat.shape}")
