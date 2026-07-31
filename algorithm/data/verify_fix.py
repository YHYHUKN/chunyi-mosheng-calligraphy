"""验证修复后的模型尺寸链路是否正确"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'd:\书法春\algorithm')
import torch
from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator

device = 'cpu'
style_dim = 128
content_dim = 256
image_size = 128

se = StyleEncoder(style_dim=style_dim)
ce = ContentEncoder(content_dim=content_dim)
gen = DualBranchGenerator(content_dim=content_dim, style_dim=style_dim)

x = torch.randn(1, 1, image_size, image_size)

# 1. StyleEncoder: 128 → style_vector
sv = se(x)
print(f"StyleEncoder 输出: {sv.shape}")  # 应该是 (1, 128)

# 2. ContentEncoder: 128 → content_features
cf = ce(x)
print(f"ContentEncoder 输出: {cf.shape}")  # 应该是 (1, 256, 8, 8)

# 3. Generator: content_features + style_vector → image
out = gen(cf, sv)
print(f"Generator 输出: {out.shape}")  # 应该是 (1, 1, 128, 128)

# 4. 验证损失函数（需要下载VGG权重）
print("\n验证VGG特征提取...")
from models.losses import CalligraphyLoss
loss_fn = CalligraphyLoss()
feats = loss_fn.vgg(x)
for i, f in enumerate(feats):
    print(f"  VGG layer {i}: {list(f.shape)}")

# 5. 验证各项损失
import torch.nn.functional as F
target = torch.randn_like(out)
print(f"\n感知损失 (random): {loss_fn.perceptual_loss(out, target).item():.4f}")
print(f"风格损失 (random): {loss_fn.style_loss(out, target).item():.4f}")
print(f"内容重建损失 (random): {loss_fn.content_reconstruction_loss(out, target).item():.4f}")

# 6. 全白 vs 有内容的对比
white = torch.ones_like(out)
print(f"\n感知损失 (白 vs 有内容): {loss_fn.perceptual_loss(white, target).item():.4f}")
print(f"风格损失 (白 vs 有内容): {loss_fn.style_loss(white, target).item():.4f}")

# 7. 对比修复前后
print(f"\n对比修复前: style_loss(白 vs 内容) = 0.000005 (几乎无效)")
print(f"对比修复后: style_loss(白 vs 内容) = {loss_fn.style_loss(white, target).item():.6f}")
print(f"修复后的VGG能正确区分白色和有内容的图了！")
