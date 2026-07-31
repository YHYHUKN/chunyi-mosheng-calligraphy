"""用赵孟頫快速验证模型生成样例图"""
import sys, os, torch, cv2, numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'd:\书法春\algorithm')
from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator

device = 'cuda'

# 加载模型
cp = torch.load(r'd:\书法春\checkpoints\final\zhao_fast_ep010.pth', map_location='cpu', weights_only=False)
cfg = cp['config']
print(f"Config: {cfg['image_size']}px, style_dim={cfg['style_dim']}")

style_enc = StyleEncoder(style_dim=cfg['style_dim']).to(device)
content_enc = ContentEncoder(content_dim=cfg['content_dim']).to(device)
gen = DualBranchGenerator(content_dim=cfg['content_dim'], style_dim=cfg['style_dim'], image_size=cfg['image_size']).to(device)

style_enc.load_state_dict(cp['style_encoder'])
content_enc.load_state_dict(cp['content_encoder'])
gen.load_state_dict(cp['generator'])
style_enc.eval(); content_enc.eval(); gen.eval()

# 加载一张赵孟頫的真实书法作为风格参考
from PIL import Image
import glob
zhao_dir = r'd:\书法春\algorithm\data\赵孟頫'
imgs = glob.glob(os.path.join(zhao_dir, '*.jpg')) + glob.glob(os.path.join(zhao_dir, '*.png'))
print(f"找到 {len(imgs)} 张赵孟頫数据")

# 生成多个样例
os.makedirs(r'd:\书法春\checkpoints\samples', exist_ok=True)

for i in range(min(6, len(imgs))):
    ref = np.array(Image.open(imgs[i]).convert('L'))
    ref = cv2.resize(ref, (cfg['image_size'], cfg['image_size']))
    ref_t = torch.from_numpy(ref.astype(np.float32) / 127.5 - 1.0).unsqueeze(0).unsqueeze(0).to(device)
    
    with torch.no_grad():
        sv = style_enc(ref_t)
        # 用一个简单骨架（十字+横竖）
        skel = np.ones((cfg['image_size'], cfg['image_size']), dtype=np.uint8) * 255
        skel[cfg['image_size']//4:cfg['image_size']//4+3, cfg['image_size']//4:3*cfg['image_size']//4] = 0
        skel[cfg['image_size']//4:3*cfg['image_size']//4, cfg['image_size']//2-1:cfg['image_size']//2+2] = 0
        skel_t = torch.from_numpy(skel.astype(np.float32) / 127.5 - 1.0).unsqueeze(0).unsqueeze(0).to(device)
        cf = content_enc(skel_t)
        out = gen(cf, sv)
    
    img = ((out.squeeze().cpu().numpy() + 1) * 127.5).clip(0, 255).astype(np.uint8)
    from PIL import Image as PILImage
    out_path = rf'd:\书法春\checkpoints\samples\zhao_sample_{i}.png'
    PILImage.fromarray(img).save(out_path)
    # 同时保存参考图
    PILImage.fromarray(ref).save(rf'd:\书法春\checkpoints\samples\zhao_ref_{i}.png')
    print(f"  样例 {i}: {out_path}")

print("\n完成！查看 checkpoints/samples/ 目录")
