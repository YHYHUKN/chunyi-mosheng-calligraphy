"""测试VGG感知损失在128x128灰度书法图上的行为"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, r'd:\书法春\algorithm')
from models.losses import CalligraphyLoss

device = 'cuda' if torch.cuda.is_available() else 'cpu'

# 创建损失函数
loss_fn = CalligraphyLoss()

# 1. 创建一个模拟的书法图（白底黑字）
def make_fake_calligraphy(size=128):
    img = np.ones((size, size), dtype=np.uint8) * 255
    # 画一个简单的"一"字（一条横线）
    img[50:70, 20:108] = 0
    # 画一个"丨"（一条竖线）
    img[20:108, 58:68] = 0
    return img

# 创建两个"书法图"
target_arr = make_fake_calligraphy()
generated_arr = make_fake_calligraphy()

# 转为tensor [-1, 1]
target_t = torch.from_numpy(target_arr.astype(np.float32)).unsqueeze(0).unsqueeze(0) / 127.5 - 1.0
gen_t = torch.from_numpy(generated_arr.astype(np.float32)).unsqueeze(0).unsqueeze(0) / 127.5 - 1.0

target_t = target_t.to(device)
gen_t = gen_t.to(device)

# 2. 测试感知损失
print("=== VGG感知损失测试 ===")
print(f"target range: [{target_t.min():.3f}, {target_t.max():.3f}]")
print(f"generated range: [{gen_t.min():.3f}, {gen_t.max():.3f}]")

perc_loss = loss_fn.perceptual_loss(gen_t, target_t)
print(f"感知损失 (相同图): {perc_loss.item():.4f}")

# 3. 创建一个全白图（模拟模型输出的全白）
white_arr = np.ones((128, 128), dtype=np.uint8) * 255
white_t = torch.from_numpy(white_arr.astype(np.float32)).unsqueeze(0).unsqueeze(0) / 127.5 - 1.0
white_t = white_t.to(device)

perc_loss_white = loss_fn.perceptual_loss(white_t, target_t)
print(f"感知损失 (全白 vs 书法): {perc_loss_white.item():.4f}")

# 4. 测试风格损失
style_loss_same = loss_fn.style_loss(gen_t, target_t)
print(f"风格损失 (相同图): {style_loss_same.item():.4f}")

style_loss_white = loss_fn.style_loss(white_t, target_t)
print(f"风格损失 (全白 vs 书法): {style_loss_white.item():.4f}")

# 5. 测试内容重建损失
content_loss_same = loss_fn.content_reconstruction_loss(gen_t, target_t)
print(f"内容损失 (相同图): {content_loss_same.item():.4f}")

content_loss_white = loss_fn.content_reconstruction_loss(white_t, target_t)
print(f"内容损失 (全白 vs 书法): {content_loss_white.item():.4f}")

# 6. 检查VGG是否能正确处理灰度输入
print("\n=== VGG特征提取测试 ===")
try:
    feats = loss_fn.vgg(gen_t)
    for i, f in enumerate(feats):
        print(f"  VGG层{i}: shape={list(f.shape)}, range=[{f.min():.3f}, {f.max():.3f}]")
except Exception as e:
    print(f"  VGG错误: {e}")

# 7. 综合检查：看看生成器输出全是~1.0时，各种loss是多少
print("\n=== 关键问题诊断 ===")
print("生成器最终层是 Tanh()，输出范围 [-1, 1]")
print("如果生成器倾向于输出全白（≈1.0）：")
print(f"  全白图的tensor值: {white_t[0,0,0,0]:.3f}")
print(f"  书法图的tensor值（黑笔画处）: {target_t[0,0,50,60]:.3f}")
print(f"  书法图的tensor值（白色处）: {target_t[0,0,10,10]:.3f}")
print()
print("全白输出 vs 真实书法的loss应该很大，生成器应该被纠正")
print(f"  内容损失L1: {content_loss_white.item():.4f} (应该很大)")
print(f"  但如果VGG输出NaN或不合理值，感知损失可能主导训练方向...")
