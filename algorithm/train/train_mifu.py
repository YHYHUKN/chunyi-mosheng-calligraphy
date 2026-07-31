"""
米芾单风格训练 — 快速出可辨识字形
128px + 30ep + batch8 + aug×6 → 100张变成600+张，约3小时
"""
import os, sys, time, json
from pathlib import Path

TRAIN_DIR   = Path(__file__).resolve().parent
ALGO_DIR    = TRAIN_DIR.parent
PROJECT_DIR = ALGO_DIR.parent
sys.path.insert(0, str(ALGO_DIR))

import torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import cv2, numpy as np
from PIL import Image

from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator    import DualBranchGenerator, Discriminator
from models.losses       import CalligraphyLoss

CONFIG = {
    "data_root"    : str(ALGO_DIR / "data"),
    "cache_dir"    : str(ALGO_DIR / "data" / ".skeleton_cache_mifu"),
    "ckpt_dir"     : str(PROJECT_DIR / "checkpoints"),
    "image_size"   : 128,
    "style_dim"    : 128,
    "content_dim"  : 256,
    "batch_size"   : 8,
    "num_epochs"   : 30,
    "lr_g"         : 2e-4,
    "lr_d"         : 4e-4,
    "save_every"   : 5,
    "device"       : "cuda" if torch.cuda.is_available() else "cpu",
    "aug_factor"   : 6,   # 100张 → ~700张
}

STYLE_MAP = {"米芾": 0}
NUM_STYLES = 1

def extract_skeleton(gray):
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((3,3), np.uint8)
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
    if img is None: return None
    img = cv2.GaussianBlur(img, (3,3), 0)
    binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 11, 8)
    coords = cv2.findNonZero(binary)
    if coords is None: return None
    x, y, w, h = cv2.boundingRect(coords)
    pad = max(w, h) // 10
    x1 = max(0, x-pad); y1 = max(0, y-pad)
    x2 = min(img.shape[1], x+w+pad); y2 = min(img.shape[0], y+h+pad)
    cropped = img[y1:y2, x1:x2]
    canvas = np.ones((size,size), dtype=np.uint8) * 255
    scale = min(size*0.85/cropped.shape[0], size*0.85/cropped.shape[1])
    nw = int(cropped.shape[1]*scale); nh = int(cropped.shape[0]*scale)
    if nw < 4 or nh < 4: return None
    resized = cv2.resize(cropped, (nw,nh), interpolation=cv2.INTER_CUBIC)
    ox = (size-nw)//2; oy = (size-nh)//2
    canvas[oy:oy+nh, ox:ox+nw] = resized
    return canvas

def augment(img, skel, n):
    results = []
    h, w = img.shape
    for _ in range(n):
        ai, as_ = img.copy(), skel.copy()
        # 旋转
        angle = np.random.uniform(-8, 8)
        M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
        ai = cv2.warpAffine(ai, M, (w,h), borderValue=255)
        as_ = cv2.warpAffine(as_, M, (w,h), borderValue=0)
        # 弹性变形
        if np.random.random() > 0.4:
            sigma = 3; alpha = 8
            dx = cv2.GaussianBlur(np.random.uniform(-1,1,(h,w)).astype(np.float32),(0,0),sigma)*alpha
            dy = cv2.GaussianBlur(np.random.uniform(-1,1,(h,w)).astype(np.float32),(0,0),sigma)*alpha
            gx, gy = np.meshgrid(np.arange(w), np.arange(h))
            mx = np.clip(gx+dx, 0, w-1).astype(np.float32)
            my = np.clip(gy+dy, 0, h-1).astype(np.float32)
            ai = cv2.remap(ai, mx, my, cv2.INTER_LINEAR, borderValue=255)
            as_ = cv2.remap(as_, mx, my, cv2.INTER_NEAREST, borderValue=0)
        # 亮度
        if np.random.random() > 0.4:
            a = np.random.uniform(0.8, 1.2)
            ai = np.clip(ai.astype(np.float32)*a, 0, 255).astype(np.uint8)
        # 模糊
        if np.random.random() > 0.5:
            ai = cv2.GaussianBlur(ai, (3,3), 0)
        results.append((ai, as_))
    return results

class CalligraphyDS(Dataset):
    def __init__(self, data_root, cache_dir, image_size, aug_factor, style_map):
        self.size = image_size
        self.records = []
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        total_raw = 0
        for name, label in style_map.items():
            base = Path(data_root) / name
            imgs = list(base.rglob("*.jpg")) + list(base.rglob("*.png"))
            print(f"  [{name}] 找到 {len(imgs)} 张原始图...")
            for img_path in imgs:
                cache_file = cache_path / f"{img_path.stem}_{name}.npz"
                if cache_file.exists():
                    d = np.load(str(cache_file))
                    img_arr, skel_arr = d['img'], d['skel']
                else:
                    img_arr = preprocess_image(str(img_path), image_size)
                    if img_arr is None: continue
                    skel_arr = extract_skeleton(img_arr)
                    np.savez_compressed(str(cache_file), img=img_arr, skel=skel_arr)
                self.records.append((img_arr, skel_arr, label))
                total_raw += 1
                for ai, as_ in augment(img_arr, skel_arr, aug_factor):
                    self.records.append((ai, as_, label))
        print(f"  => {len(self.records)} 样本 (原始 {total_raw} + 增强 {len(self.records)-total_raw})")

    def __len__(self): return len(self.records)
    def __getitem__(self, idx):
        img, skel, label = self.records[idx]
        img_t  = torch.from_numpy(img.astype(np.float32)/127.5 - 1.0).unsqueeze(0)
        skel_t = torch.from_numpy(skel.astype(np.float32)/127.5 - 1.0).unsqueeze(0)
        return {"image": img_t, "skeleton": skel_t, "style_label": torch.tensor(label, dtype=torch.long)}

class Trainer:
    def __init__(self, cfg):
        self.cfg = cfg
        self.dev = torch.device(cfg["device"])
        sd, cd = cfg["style_dim"], cfg["content_dim"]
        self.style_enc   = StyleEncoder(style_dim=sd).to(self.dev)
        self.content_enc = ContentEncoder(content_dim=cd).to(self.dev)
        self.gen         = DualBranchGenerator(content_dim=cd, style_dim=sd).to(self.dev)
        self.disc        = Discriminator(num_styles=NUM_STYLES).to(self.dev)
        for m in [self.style_enc, self.content_enc, self.gen, self.disc]:
            for mod in m.modules():
                if isinstance(mod, (nn.Conv2d, nn.ConvTranspose2d, nn.Linear)):
                    nn.init.xavier_uniform_(mod.weight)
                    if mod.bias is not None: nn.init.zeros_(mod.bias)
                elif isinstance(mod, (nn.InstanceNorm2d, nn.BatchNorm2d)):
                    if mod.weight is not None: nn.init.ones_(mod.weight)
                    if mod.bias is not None: nn.init.zeros_(mod.bias)
        self.loss_fn = CalligraphyLoss()
        self.opt_g = torch.optim.Adam(
            list(self.gen.parameters()) + list(self.style_enc.parameters()) +
            list(self.content_enc.parameters()), lr=cfg["lr_g"], betas=(0.5, 0.999))
        self.opt_d = torch.optim.Adam(self.disc.parameters(), lr=cfg["lr_d"], betas=(0.5, 0.999))
        self.sch_g = torch.optim.lr_scheduler.CosineAnnealingLR(self.opt_g, T_max=cfg["num_epochs"])
        self.sch_d = torch.optim.lr_scheduler.CosineAnnealingLR(self.opt_d, T_max=cfg["num_epochs"])
        p = sum(p.numel() for p in self.gen.parameters())
        print(f"  生成器参数量: {p/1e6:.2f}M  |  设备: {self.dev}")

    def train_epoch(self, loader):
        for m in [self.style_enc, self.content_enc, self.gen, self.disc]: m.train()
        lg_sum = ld_sum = n = 0
        for batch in loader:
            images = batch["image"].to(self.dev)
            skels  = batch["skeleton"].to(self.dev)
            labels = batch["style_label"].to(self.dev)
            # D step
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
            # G step
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
        return lg_sum/max(n,1), ld_sum/max(n,1)

    def save(self, epoch, ckpt_dir, tag=""):
        Path(ckpt_dir).mkdir(parents=True, exist_ok=True)
        name = f"mifu_ep{epoch:03d}{tag}.pth"
        torch.save({
            "epoch": epoch,
            "style_encoder":   self.style_enc.state_dict(),
            "content_encoder": self.content_enc.state_dict(),
            "generator":       self.gen.state_dict(),
            "discriminator":   self.disc.state_dict(),
            "config": self.cfg,
            "style_map": STYLE_MAP,
        }, os.path.join(ckpt_dir, name))
        print(f"  [SAVE] {name}")

def main():
    cfg = CONFIG
    print("=" * 60)
    print("  米芾单风格训练 (128px/30ep/batch8/aug6)")
    print(f"  数据: {cfg['data_root']}/米芾  |  设备: {cfg['device']}")
    print("=" * 60)
    print("\n[1/3] 加载数据...")
    ds = CalligraphyDS(cfg["data_root"], cfg["cache_dir"], cfg["image_size"], cfg["aug_factor"], STYLE_MAP)
    if len(ds) == 0:
        print("[ERROR] 数据集为空!"); return
    loader = DataLoader(ds, batch_size=cfg["batch_size"], shuffle=True, num_workers=0, drop_last=True)
    print(f"  {len(ds)} 样本 -> {len(loader)} batches/epoch")

    print("\n[2/3] 初始化模型...")
    trainer = Trainer(cfg)

    print(f"\n[3/3] 开始训练...")
    log = []
    best_g = float("inf")
    for epoch in range(1, cfg["num_epochs"]+1):
        t0 = time.time()
        lg, ld = trainer.train_epoch(loader)
        dt = time.time() - t0
        eta = dt * (cfg["num_epochs"] - epoch)
        log.append({"epoch": epoch, "loss_g": round(lg,4), "loss_d": round(ld,4)})
        print(f"  [{epoch:02d}/{cfg['num_epochs']}] G:{lg:.4f} D:{ld:.4f} {dt:.0f}s ETA:{int(eta//60)}m", flush=True)
        if epoch % cfg["save_every"] == 0:
            trainer.save(epoch, cfg["ckpt_dir"])
        if lg < best_g:
            best_g = lg
            trainer.save(epoch, cfg["ckpt_dir"], tag="_best")

    final_dir = os.path.join(cfg["ckpt_dir"], "final")
    trainer.save(cfg["num_epochs"], final_dir)
    with open(os.path.join(final_dir, "style_map.json"), "w", encoding="utf-8") as f:
        json.dump({"style_map": STYLE_MAP, "image_size": cfg["image_size"],
                   "style_dim": cfg["style_dim"], "content_dim": cfg["content_dim"]}, f, ensure_ascii=False, indent=2)
    print(f"\n[DONE] 最佳 G Loss: {best_g:.4f}")
    print(f"  模型: {final_dir}/mifu_ep{cfg['num_epochs']:03d}.pth")

if __name__ == "__main__":
    main()
