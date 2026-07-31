"""精确追踪融合模块的对齐情况"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import torch
import torch.nn.functional as F
sys.path.insert(0, r'd:\书法春\algorithm')
from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator

device = 'cpu'
style_dim = 128
content_dim = 256

style_enc = StyleEncoder(style_dim=style_dim)
content_enc = ContentEncoder(content_dim=content_dim)
generator = DualBranchGenerator(content_dim=content_dim, style_dim=style_dim)

img = torch.randn(2, 1, 128, 128)
skel = torch.randn(2, 1, 128, 128)

sv = style_enc(img)
cf = content_enc(skel)

B = 2

# 内容分支逐层上采样
content_feats = []
x = cf
for block in generator.content_up:
    x = block(x, sv)
    content_feats.append(x)

# 风格分支：向量→特征图→逐层上采样
style_feat = generator.style_fc(sv)
style_feat = style_feat.view(B, 64, 16, 16)
style_feats = []
for up in generator.style_up:
    style_feat = up(style_feat)
    style_feats.append(style_feat)

print("=== 融合模块对齐情况 ===")
for i, (c_feat, s_feat) in enumerate(zip(content_feats, style_feats)):
    match = "✅ 匹配" if c_feat.shape[2:] == s_feat.shape[2:] else f"❌ 不匹配 c={c_feat.shape[2:]} vs s={s_feat.shape[2:]}"
    print(f"  融合层[{i}]: content={list(c_feat.shape)} style={list(s_feat.shape)} {match}")
    if c_feat.shape[2:] != s_feat.shape[2:]:
        s_aligned = F.interpolate(s_feat, size=c_feat.shape[2:], mode='nearest')
        print(f"    → 风格特征被插值到: {list(s_aligned.shape)}")

# 检查最终融合后的特征
fused = None
for i, (c_feat, s_feat) in enumerate(zip(content_feats, style_feats)):
    if c_feat.shape[2:] != s_feat.shape[2:]:
        s_feat = F.interpolate(s_feat, size=c_feat.shape[2:], mode='nearest')
    merged = generator.fusions[i](c_feat, s_feat)
    fused = merged
    print(f"\n  融合后[{i}]: {list(fused.shape)}")

output = generator.output_conv(fused)
print(f"\n最终输出: {list(output.shape)}")

# 现在检查损失函数中的感知损失——VGG在处理128x128 vs 256x256时的行为
print("\n=== 风格分支设计问题 ===")
print("风格分支从16x16上采样到256x256，但内容分支从8x8到128x128")
print("这意味着在后面的融合层，风格特征需要被大幅下采样到128x128")
print("最后content_up[3]是128x128，但style_up[3]是256x256")
print("融合时256x256的风格特征被下采样到128x128 → 风格信息严重丢失！")
