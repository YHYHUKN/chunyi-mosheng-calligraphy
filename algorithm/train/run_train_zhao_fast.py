"""
单风格快速验证训练 — 只训赵孟頫，尽快看到结果
激进参数: 64x64, 10 epochs, batch 16, 1x增强
"""
import os, sys, time, json
from pathlib import Path

TRAIN_DIR   = Path(__file__).resolve().parent
ALGO_DIR    = TRAIN_DIR.parent
PROJECT_DIR = ALGO_DIR.parent
sys.path.insert(0, str(ALGO_DIR))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
from PIL import Image

from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator    import DualBranchGenerator, Discriminator
from models.losses       import CalligraphyLoss

# ===========================================================
#  激进配置
# ===========================================================
CONFIG = {
    "data_root"    : str(ALGO_DIR / "data"),
    "cache_dir"    : str(ALGO_DIR / "data" / ".skeleton_cache_zhao64"),
    "ckpt_dir"     : str(PROJECT_DIR / "checkpoints"),
    "image_size"   : 64,       # 64x64 加速4x
    "style_dim"    : 128,
    "content_dim"  : 256,
    "batch_size"   : 16,       # 大batch加速
    "num_epochs"   : 10,       # 快速验证
    "lr_g"         : 2e-4,
    "lr_d"         : 4e-4,
    "save_every"   : 2,
    "device"       : "cuda" if torch.cuda.is_available() else "cpu",
    "aug_factor"   : 1,        # 不增强，最快
}

# 只训赵孟頫
STYLE_MAP = {"赵孟頫": 0}
NUM_STYLES = 1

# ===========================================================
#  骨架提取 & 预处理（复用）
# ===========================================================
def extract_skeleton(gray):
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    try:
        skeleton = cv2.ximgproc.thinning(binary)
    except:
        skeleton = binary
    skeleton = cv2.dilate(skeleton, kernel, iterations=1)
    return skeleton

def _imread_unicode(path):
    try:
        return np.array(Image.open(path).convert("L"))
    except:
        return None

def preprocess_image(path, size):
    img = _imread_unicode(path)
    if img is None:
        return None
    img = cv2.GaussianBlur(img, (3, 3), 0)
    binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 8)
    coords = cv2.findNonZero(binary)
    if coords is None:
        return None
    x, y, w, h = cv2.boundingRect(coords)
    pad = max(w, h) // 10
    x1, y1 = max(0, x-pad), max(0, y-pad)
    x2, y2 = min(img.shape[1], x+w+pad), min(img.shape[0], y+h+pad)
    cropped = img[y1:y2, x1:x2]
    canvas = np.ones((size, size), dtype=np.uint8) * 255
    scale = min(size * 0.85 / cropped.shape[0], size * 0.85 / cropped.shape[1])
    nw, nh = int(cropped.shape[1] * scale), int(cropped.shape[0] * scale)
    if nw < 4 or nh < 4:
        return None
    resized = cv2.resize(cropped, (nw, nh), interpolation=cv2.INTER_CUBIC)
    ox, oy = (size - nw) // 2, (size - nh) // 2
    canvas[oy:oy+nh, ox:ox+nw] = resized
    return canvas

# ===========================================================
#  Dataset
# ===========================================================
class CalligraphyDS(Dataset):
    def __init__(self, data_root, cache_dir, image_size, style_map):
        self.size = image_size
        self.records = []
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        total = 0
        for name, label in style_map.items():
            base = Path(data_root) / name
            imgs = list(base.rglob("*.jpg")) + list(base.rglob("*.png"))
            print(f"  [{name}] {len(imgs)} 张图...")
            for img_path in imgs:
                cache_file = cache_path / f"{img_path.stem}_{name}.npz"
                if cache_file.exists():
                    d = np.load(str(cache_file))
                    img_arr, skel_arr = d['img'], d['skel']
                else:
                    img_arr = preprocess_image(str(img_path), image_size)
                    if img_arr is None:
                        continue
                    skel_arr = extract_skeleton(img_arr)
                    np.savez_compressed(str(cache_file), img=img_arr, skel=skel_arr)
                self.records.append((img_arr, skel_arr, label))
                total += 1
        print(f"  -> {len(self.records)} 张 (无增强)")

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        img, skel, label = self.records[idx]
        img_t  = torch.from_numpy(img.astype(np.float32)  / 127.5 - 1.0).unsqueeze(0)
        skel_t = torch.from_numpy(skel.astype(np.float32) / 127.5 - 1.0).unsqueeze(0)
        return {"image": img_t, "skeleton": skel_t, "style_label": torch.tensor(label, dtype=torch.long)}

# ===========================================================
#  Trainer
# ===========================================================
class Trainer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.dev = torch.device(cfg["device"])
        sd, cd = cfg["style_dim"], cfg["content_dim"]
        self.style_enc   = StyleEncoder(style_dim=sd).to(self.dev)
        self.content_enc = ContentEncoder(content_dim=cd).to(self.dev)
        self.gen         = DualBranchGenerator(content_dim=cd, style_dim=sd, image_size=cfg["image_size"]).to(self.dev)
        self.disc        = Discriminator(num_styles=NUM_STYLES).to(self.dev)
        for m in [self.style_enc, self.content_enc, self.gen, self.disc]:
            self._init_w(m)
        self.loss_fn = CalligraphyLoss()
        self.opt_g = torch.optim.Adam(
            list(self.gen.parameters()) + list(self.style_enc.parameters()) + list(self.content_enc.parameters()),
            lr=cfg["lr_g"], betas=(0.5, 0.999))
        self.opt_d = torch.optim.Adam(self.disc.parameters(), lr=cfg["lr_d"], betas=(0.5, 0.999))
        self.sch_g = torch.optim.lr_scheduler.CosineAnnealingLR(self.opt_g, T_max=cfg["num_epochs"])
        self.sch_d = torch.optim.lr_scheduler.CosineAnnealingLR(self.opt_d, T_max=cfg["num_epochs"])
        p = sum(p.numel() for p in self.gen.parameters())
        print(f"  生成器参数: {p/1e6:.2f}M | {self.dev}")

    def _init_w(self, model):
        for m in model.modules():
            if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d, nn.Linear)):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None: nn.init.zeros_(m.bias)
            elif isinstance(m, (nn.InstanceNorm2d, nn.BatchNorm2d)):
                if m.weight is not None: nn.init.ones_(m.weight)
                if m.bias is not None: nn.init.zeros_(m.bias)

    def train_epoch(self, loader):
        for m in [self.style_enc, self.content_enc, self.gen, self.disc]:
            m.train()
        lg_sum = ld_sum = n = 0
        for batch in loader:
            images = batch["image"].to(self.dev)
            skels  = batch["skeleton"].to(self.dev)
            labels = batch["style_label"].to(self.dev)
            # 判别器
            self.opt_d.zero_grad()
            with torch.no_grad():
                sv = self.style_enc(images)
                cf = self.content_enc(skels)
                fake = self.gen(cf, sv)
            d_real_adv, d_real_cls = self.disc(images)
            d_fake_adv, _          = self.disc(fake.detach())
            loss_d, _ = self.loss_fn.compute_discriminator_loss(d_real_adv, d_fake_adv, d_real_cls, labels)
            loss_d = loss_d + F.cross_entropy(d_real_cls, labels)
            loss_d.backward()
            self.opt_d.step()
            # 生成器
            self.opt_g.zero_grad()
            sv = self.style_enc(images)
            cf = self.content_enc(skels)
            fake = self.gen(cf, sv)
            d_fake_adv, d_fake_cls = self.disc(fake)
            loss_g, _ = self.loss_fn.compute_generator_loss(fake, images, images, d_fake_adv, d_fake_cls, labels)
            loss_g.backward()
            torch.nn.utils.clip_grad_norm_(list(self.gen.parameters()) + list(self.style_enc.parameters()), 1.0)
            self.opt_g.step()
            lg_sum += loss_g.item(); ld_sum += loss_d.item(); n += 1
        self.sch_g.step(); self.sch_d.step()
        return lg_sum / max(n, 1), ld_sum / max(n, 1)

    def save(self, epoch, ckpt_dir, tag=""):
        Path(ckpt_dir).mkdir(parents=True, exist_ok=True)
        name = f"zhao_fast_ep{epoch:03d}{tag}.pth"
        torch.save({
            "epoch": epoch,
            "style_encoder":   self.style_enc.state_dict(),
            "content_encoder": self.content_enc.state_dict(),
            "generator":       self.gen.state_dict(),
            "discriminator":   self.disc.state_dict(),
            "config":          self.cfg,
            "style_map":       STYLE_MAP,
        }, os.path.join(ckpt_dir, name))
        print(f"  [SAVE] {name}")

    @torch.no_grad()
    def generate_sample(self):
        """每epoch结束后生成一张样例看效果"""
        self.gen.eval()
        dummy = torch.randn(1, 1, self.cfg["image_size"], self.cfg["image_size"]).to(self.dev)
        sv = self.style_enc(dummy)
        cf = self.content_enc(dummy)
        out = self.gen(cf, sv)
        img = ((out.squeeze().cpu().numpy() + 1) * 127.5).clip(0, 255).astype(np.uint8)
        # 保存样例
        sample_dir = Path(self.cfg["ckpt_dir"]) / "samples"
        sample_dir.mkdir(exist_ok=True)
        cv2.imwrite(str(sample_dir / "zhao_sample_latest.png"), img)
        return img

# ===========================================================
#  Main
# ===========================================================
def main():
    cfg = CONFIG
    print("=" * 60)
    print("  春意墨生 — 赵孟頫快速验证")
    print(f"  尺寸: {cfg['image_size']}x{cfg['image_size']}  Batch: {cfg['batch_size']}  Epochs: {cfg['num_epochs']}")
    print(f"  数据: 只训赵孟頫 ({len(STYLE_MAP)}风格)")
    print(f"  设备: {cfg['device']}")
    print("=" * 60)

    print("\n[1/3] 加载数据...")
    ds = CalligraphyDS(cfg["data_root"], cfg["cache_dir"], cfg["image_size"], STYLE_MAP)
    if len(ds) == 0:
        print("[ERROR] 数据为空！"); return
    loader = DataLoader(ds, batch_size=cfg["batch_size"], shuffle=True, num_workers=0, drop_last=True)
    print(f"  {len(ds)} 样本 -> {len(loader)} batches/epoch")

    print("\n[2/3] 初始化模型...")
    trainer = Trainer(cfg)

    print(f"\n[3/3] 开始训练 ({cfg['num_epochs']} epochs)...")
    best_g = float("inf")
    log = []
    for epoch in range(1, cfg["num_epochs"] + 1):
        t0 = time.time()
        lg, ld = trainer.train_epoch(loader)
        dt = time.time() - t0
        eta = dt * (cfg["num_epochs"] - epoch)
        # 生成样例
        trainer.generate_sample()
        print(f"  Epoch [{epoch:02d}/{cfg['num_epochs']}] G:{lg:.4f} D:{ld:.4f} {dt:.0f}s ETA:{int(eta//60)}m")
        log.append({"epoch": epoch, "G": round(lg,4), "D": round(ld,4)})
        if epoch % cfg["save_every"] == 0:
            trainer.save(epoch, cfg["ckpt_dir"])
        if lg < best_g:
            best_g = lg
            trainer.save(epoch, cfg["ckpt_dir"], tag="_best")

    # 最终模型
    final_dir = os.path.join(cfg["ckpt_dir"], "final")
    Path(final_dir).mkdir(parents=True, exist_ok=True)
    trainer.save(cfg["num_epochs"], final_dir)
    with open(os.path.join(final_dir, "style_map.json"), "w", encoding="utf-8") as f:
        json.dump({"style_map": STYLE_MAP, "image_size": cfg["image_size"],
                   "style_dim": cfg["style_dim"], "content_dim": cfg["content_dim"]}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(cfg["ckpt_dir"], "train_log_zhao_fast.json"), "w") as f:
        json.dump(log, f, indent=2)

    print(f"\n[DONE] 最佳 G Loss: {best_g:.4f}")
    print(f"  样例图: checkpoints/samples/zhao_sample_latest.png")
    print(f"  模型: checkpoints/final/zhao_fast_ep{cfg['num_epochs']:03d}.pth")

if __name__ == "__main__":
    main()
