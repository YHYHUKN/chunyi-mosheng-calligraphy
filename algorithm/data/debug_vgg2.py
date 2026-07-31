import sys, os
sys.stdout.reconfigure(encoding='utf-8')

# 禁用所有warning
import warnings
warnings.filterwarnings('ignore')
os.environ['TORCH_WARNINGS'] = '0'

import torch
import torch.nn.functional as F
import numpy as np
sys.path.insert(0, r'd:\书法春\algorithm')
from models.losses import CalligraphyLoss

device = 'cuda' if torch.cuda.is_available() else 'cpu'

loss_fn = CalligraphyLoss()

# 创建两个"书法图"（白底黑字）
def make_fake_calligraphy(size=128):
    img = np.ones((size, size), dtype=np.uint8) * 255
    img[50:70, 20:108] = 0
    img[20:108, 58:68] = 0
    return img

target_arr = make_fake_calligraphy()
generated_arr = make_fake_calligraphy()

target_t = torch.from_numpy(target_arr.astype(np.float32)).unsqueeze(0).unsqueeze(0) / 127.5 - 1.0
gen_t = torch.from_numpy(generated_arr.astype(np.float32)).unsqueeze(0).unsqueeze(0) / 127.5 - 1.0
target_t = target_t.to(device)
gen_t = gen_t.to(device)

# 全白图
white_arr = np.ones((128, 128), dtype=np.uint8) * 255
white_t = torch.from_numpy(white_arr.astype(np.float32)).unsqueeze(0).unsqueeze(0) / 127.5 - 1.0
white_t = white_t.to(device)

print("=== VGG Feature Test ===")
try:
    feats = loss_fn.vgg(gen_t)
    for i, f in enumerate(feats):
        has_nan = torch.isnan(f).any().item()
        has_inf = torch.isinf(f).any().item()
        print(f"  VGG layer {i}: shape={list(f.shape)}, nan={has_nan}, inf={has_inf}, range=[{f.min():.3f}, {f.max():.3f}]")
except Exception as e:
    print(f"  VGG ERROR: {e}")

print("\n=== Loss Test ===")
perc_loss = loss_fn.perceptual_loss(gen_t, target_t)
print(f"perc_loss (same): {perc_loss.item():.6f}")

perc_loss_white = loss_fn.perceptual_loss(white_t, target_t)
print(f"perc_loss (white vs calli): {perc_loss_white.item():.6f}")
print(f"  has NaN: {torch.isnan(perc_loss_white).item()}")

style_loss_white = loss_fn.style_loss(white_t, target_t)
print(f"style_loss (white vs calli): {style_loss_white.item():.6f}")
print(f"  has NaN: {torch.isnan(style_loss_white).item()}")

content_loss_white = loss_fn.content_reconstruction_loss(white_t, target_t)
print(f"content_loss (white vs calli): {content_loss_white.item():.6f}")

print("\n=== Diagnosis ===")
if torch.isnan(perc_loss_white).item() or perc_loss_white.item() == 0:
    print("PROBLEM: VGG perceptual loss is NaN or zero!")
    print("VGG pretrained=False means weights are random!")
    print("Random VGG features are meaningless for perceptual loss")
    print("This causes unstable training!")

# Check VGG weights
vgg_first_layer = list(loss_fn.vgg.blocks[0][0].parameters())[0]
print(f"\nVGG first conv weight range: [{vgg_first_layer.min():.6f}, {vgg_first_layer.max():.6f}]")
print(f"VGG first conv weight mean: {vgg_first_layer.mean():.6f}")
