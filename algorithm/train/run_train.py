"""
书法GAN完整训练脚本
用法: python algorithm/train/run_train.py
- 自动扫描 algorithm/data/ 目录加载6种风格数据
- 提取骨架并缓存到 algorithm/data/.skeleton_cache/
- 训练完成后保存到 checkpoints/final.pth
"""
import os, sys, time, json
from pathlib import Path

# ---- 路径设置 ----
TRAIN_DIR   = Path(__file__).resolve().parent          # algorithm/train
ALGO_DIR    = TRAIN_DIR.parent                          # algorithm
PROJECT_DIR = ALGO_DIR.parent                           # d:\书法春
sys.path.insert(0, str(ALGO_DIR))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import cv2
import numpy as np
from PIL import Image

# ---- 导入项目模块 ----
from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator    import DualBranchGenerator, Discriminator
from models.losses       import CalligraphyLoss

# ===========================================================
#  配置
# ===========================================================
CONFIG = {
    # 路径
    "data_root"    : str(ALGO_DIR / "data"),
    "cache_dir"    : str(ALGO_DIR / "data" / ".skeleton_cache"),
    "ckpt_dir"     : str(PROJECT_DIR / "checkpoints"),
    # 模型 —— 与 generator.py / style_encoder.py 默认值保持一致
    "image_size"   : 128,      # CPU 友好，128×128
    "style_dim"    : 128,      # StyleEncoder 默认 style_dim=128
    "content_dim"  : 256,      # ContentEncoder 默认 content_dim=256
    # 训练 —— 适配 4GB 显存 + 合成数据（1440张）
    "batch_size"   : 8,
    "num_epochs"   : 5,       # 修复测试：先跑5 epoch验证
    "lr_g"         : 2e-4,     # 标准学习率
    "lr_d"         : 4e-4,
    "save_every"   : 1,
    "device"       : "cuda" if torch.cuda.is_available() else "cpu",
    # 合成数据已有增强，不再重复
    "aug_factor"   : 1,
}

# 6种风格名与标签
STYLE_MAP = {
    "米芾":   0,
    "赵孟頫": 1,
    "褚遂良": 2,
    "乙瑛碑": 3,
    "邓石如": 4,
    "怀素":   5,
}
NUM_STYLES = len(STYLE_MAP)

# ===========================================================
#  骨架提取（Zhang-Suen细化）
# ===========================================================
def extract_skeleton(gray: np.ndarray) -> np.ndarray:
    """灰度图 → 骨架二值图"""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # 形态学降噪
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    # Zhang-Suen 细化
    try:
        skeleton = cv2.ximgproc.thinning(binary)
    except Exception:
        skeleton = binary  # fallback
    # 膨胀1px保证连续
    skeleton = cv2.dilate(skeleton, kernel, iterations=1)
    return skeleton


def _imread_unicode(path: str) -> np.ndarray | None:
    """用 PIL 绕过 OpenCV 中文路径问题"""
    try:
        pil = Image.open(path).convert("L")
        return np.array(pil)
    except Exception:
        return None


def preprocess_image(path: str, size: int) -> np.ndarray | None:
    """读取 → 灰度 → 去噪 → 裁切 → 缩放到 size×size"""
    img = _imread_unicode(path)
    if img is None:
        return None
    img = cv2.GaussianBlur(img, (3, 3), 0)
    binary = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 8
    )
    coords = cv2.findNonZero(binary)
    if coords is None:
        return None
    x, y, w, h = cv2.boundingRect(coords)
    pad = max(w, h) // 10
    x1 = max(0, x - pad); y1 = max(0, y - pad)
    x2 = min(img.shape[1], x + w + pad); y2 = min(img.shape[0], y + h + pad)
    cropped = img[y1:y2, x1:x2]
    canvas = np.ones((size, size), dtype=np.uint8) * 255
    scale = min(size * 0.85 / cropped.shape[0], size * 0.85 / cropped.shape[1])
    nw = int(cropped.shape[1] * scale); nh = int(cropped.shape[0] * scale)
    if nw < 4 or nh < 4:
        return None
    resized = cv2.resize(cropped, (nw, nh), interpolation=cv2.INTER_CUBIC)
    ox = (size - nw) // 2; oy = (size - nh) // 2
    canvas[oy:oy+nh, ox:ox+nw] = resized
    return canvas


# ===========================================================
#  数据增强
# ===========================================================
def augment(img: np.ndarray, skel: np.ndarray, n: int):
    results = []
    h, w = img.shape
    for _ in range(n):
        angle = np.random.uniform(-8, 8)
        M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
        ai = cv2.warpAffine(img,  M, (w, h), borderValue=255)
        as_ = cv2.warpAffine(skel, M, (w, h), borderValue=0)
        # 弹性形变
        if np.random.random() > 0.4:
            sigma = 3; alpha = 8
            dx = cv2.GaussianBlur(np.random.uniform(-1,1,(h,w)).astype(np.float32),(0,0),sigma)*alpha
            dy = cv2.GaussianBlur(np.random.uniform(-1,1,(h,w)).astype(np.float32),(0,0),sigma)*alpha
            gx, gy = np.meshgrid(np.arange(w), np.arange(h))
            mx = np.clip(gx+dx, 0, w-1).astype(np.float32)
            my = np.clip(gy+dy, 0, h-1).astype(np.float32)
            ai  = cv2.remap(ai,  mx, my, cv2.INTER_LINEAR,  borderValue=255)
            as_ = cv2.remap(as_, mx, my, cv2.INTER_NEAREST, borderValue=0)
        # 随机亮度
        if np.random.random() > 0.3:
            a = np.random.uniform(0.75, 1.25)
            ai = np.clip(ai.astype(np.float32) * a, 0, 255).astype(np.uint8)
        # 随机模糊
        if np.random.random() > 0.5:
            ai = cv2.GaussianBlur(ai, (3,3), 0)
        results.append((ai, as_))
    return results


# ===========================================================
#  Dataset
# ===========================================================
class CalligraphyDS(Dataset):
    def __init__(self, data_root, cache_dir, image_size, aug_factor, style_map):
        self.size = image_size
        self.records = []  # (img_arr, skel_arr, label)
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

        total_raw = 0
        for name, label in style_map.items():
            # 找到 data/书法家名/书体/ 目录下所有图片
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
                    if img_arr is None:
                        continue
                    skel_arr = extract_skeleton(img_arr)
                    np.savez_compressed(str(cache_file), img=img_arr, skel=skel_arr)

                # 原始图
                self.records.append((img_arr, skel_arr, label))
                total_raw += 1
                # 数据增强
                for ai, as_ in augment(img_arr, skel_arr, aug_factor):
                    self.records.append((ai, as_, label))

        print(f"  → 总计 {len(self.records)} 条样本（原始 {total_raw} + 增强 {len(self.records)-total_raw}）")

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        img, skel, label = self.records[idx]
        # 归一化到 [-1, 1]，添加通道维
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
        sz  = cfg["image_size"]
        sd  = cfg["style_dim"]
        cd  = cfg["content_dim"]

        self.style_enc   = StyleEncoder(style_dim=sd).to(self.dev)
        self.content_enc = ContentEncoder(content_dim=cd).to(self.dev)
        self.gen         = DualBranchGenerator(content_dim=cd, style_dim=sd, image_size=cfg["image_size"]).to(self.dev)
        self.disc        = Discriminator(num_styles=NUM_STYLES).to(self.dev)

        for m in [self.style_enc, self.content_enc, self.gen, self.disc]:
            self._init_w(m)

        self.loss_fn = CalligraphyLoss()
        self.opt_g   = torch.optim.Adam(
            list(self.gen.parameters()) +
            list(self.style_enc.parameters()) +
            list(self.content_enc.parameters()),
            lr=cfg["lr_g"], betas=(0.5, 0.999))
        self.opt_d   = torch.optim.Adam(self.disc.parameters(), lr=cfg["lr_d"], betas=(0.5, 0.999))
        self.sch_g   = torch.optim.lr_scheduler.CosineAnnealingLR(self.opt_g, T_max=cfg["num_epochs"])
        self.sch_d   = torch.optim.lr_scheduler.CosineAnnealingLR(self.opt_d, T_max=cfg["num_epochs"])

        p = sum(p.numel() for p in self.gen.parameters())
        print(f"  生成器参数量: {p/1e6:.2f}M  |  设备: {self.dev}")

    def _init_w(self, model):
        for m in model.modules():
            if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d, nn.Linear)):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None: nn.init.zeros_(m.bias)
            elif isinstance(m, (nn.InstanceNorm2d, nn.BatchNorm2d)):
                if m.weight is not None: nn.init.ones_(m.weight)
                if m.bias  is not None: nn.init.zeros_(m.bias)

    def train_epoch(self, loader):
        for m in [self.style_enc, self.content_enc, self.gen, self.disc]:
            m.train()
        lg_sum = ld_sum = n = 0

        for batch in loader:
            images = batch["image"].to(self.dev)
            skels  = batch["skeleton"].to(self.dev)
            labels = batch["style_label"].to(self.dev)
            B = images.size(0)

            # ---- 判别器 ----
            self.opt_d.zero_grad()
            with torch.no_grad():
                sv = self.style_enc(images)
                cf = self.content_enc(skels)
                fake = self.gen(cf, sv)
            d_real_adv, d_real_cls = self.disc(images)
            d_fake_adv, _          = self.disc(fake.detach())

            loss_d, dm = self.loss_fn.compute_discriminator_loss(
                d_real_adv, d_fake_adv, d_real_cls, labels)
            loss_d = loss_d + F.cross_entropy(d_real_cls, labels)
            loss_d.backward()
            self.opt_d.step()

            # ---- 生成器 ----
            self.opt_g.zero_grad()
            sv   = self.style_enc(images)
            cf   = self.content_enc(skels)
            fake = self.gen(cf, sv)
            d_fake_adv, d_fake_cls = self.disc(fake)

            loss_g, gm = self.loss_fn.compute_generator_loss(
                fake, images, images, d_fake_adv, d_fake_cls, labels)
            loss_g.backward()
            torch.nn.utils.clip_grad_norm_(list(self.gen.parameters()) +
                                           list(self.style_enc.parameters()), 1.0)
            self.opt_g.step()

            lg_sum += loss_g.item(); ld_sum += loss_d.item(); n += 1

        self.sch_g.step(); self.sch_d.step()
        return lg_sum/max(n,1), ld_sum/max(n,1)

    def save(self, epoch, ckpt_dir, tag=""):
        Path(ckpt_dir).mkdir(parents=True, exist_ok=True)
        name = f"checkpoint_epoch_{epoch:03d}{tag}.pth"
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

    # ---- 推理：给定风格标签生成一张图 ----
    @torch.no_grad()
    def generate_by_style(self, style_label: int, ref_loader=None):
        self.gen.eval(); self.style_enc.eval(); self.content_enc.eval()
        # 用一个随机噪声做骨架（推理时无实际骨架）
        dummy_skel = torch.randn(1, 1, self.cfg["image_size"], self.cfg["image_size"]).to(self.dev)
        # 风格向量：从随机向量出发（训练后可换成真实参考图）
        dummy_img  = torch.randn(1, 1, self.cfg["image_size"], self.cfg["image_size"]).to(self.dev)
        sv = self.style_enc(dummy_img)
        cf = self.content_enc(dummy_skel)
        out = self.gen(cf, sv)
        img = ((out.squeeze().cpu().numpy() + 1) * 127.5).clip(0, 255).astype(np.uint8)
        return img


# ===========================================================
#  Main
# ===========================================================
def main():
    cfg = CONFIG
    print("=" * 60)
    print("  春意墨生 — AI书法模型训练")
    print(f"  数据目录  : {cfg['data_root']}")
    print(f"  图片尺寸  : {cfg['image_size']}×{cfg['image_size']}")
    print(f"  Batch     : {cfg['batch_size']}   Epoch: {cfg['num_epochs']}")
    print(f"  设备      : {cfg['device']}")
    print("=" * 60)

    # ---- 数据集 ----
    print("\n[1/3] 加载数据集...")
    ds = CalligraphyDS(
        data_root  = cfg["data_root"],
        cache_dir  = cfg["cache_dir"],
        image_size = cfg["image_size"],
        aug_factor = cfg["aug_factor"],
        style_map  = STYLE_MAP,
    )
    if len(ds) == 0:
        print("[ERROR] 数据集为空，请检查 algorithm/data/ 目录！")
        return

    loader = DataLoader(ds, batch_size=cfg["batch_size"],
                        shuffle=True, num_workers=0, drop_last=True)
    print(f"  DataLoader: {len(ds)} 样本 → {len(loader)} batches/epoch")

    # ---- 模型 ----
    print("\n[2/3] 初始化模型...")
    trainer = Trainer(cfg)

    # ---- 训练 ----
    print(f"\n[3/3] 开始训练 ({cfg['num_epochs']} epochs)...")
    log = []
    best_g = float("inf")

    for epoch in range(1, cfg["num_epochs"] + 1):
        t0 = time.time()
        lg, ld = trainer.train_epoch(loader)
        dt = time.time() - t0
        eta_sec = dt * (cfg["num_epochs"] - epoch)
        eta_str = f"{int(eta_sec//3600)}h{int((eta_sec%3600)//60)}m"

        log.append({"epoch": epoch, "loss_g": round(lg,4), "loss_d": round(ld,4)})
        print(f"  Epoch [{epoch:03d}/{cfg['num_epochs']}] "
              f"G: {lg:.4f}  D: {ld:.4f}  "
              f"耗时: {dt:.0f}s  ETA: {eta_str}")

        if epoch % cfg["save_every"] == 0:
            trainer.save(epoch, cfg["ckpt_dir"])

        if lg < best_g:
            best_g = lg
            trainer.save(epoch, cfg["ckpt_dir"], tag="_best")

    # ---- 保存最终模型 ----
    final_dir = os.path.join(cfg["ckpt_dir"], "final")
    trainer.save(cfg["num_epochs"], final_dir)

    # 写一份 style_map.json，供 app.py 推理使用
    with open(os.path.join(final_dir, "style_map.json"), "w", encoding="utf-8") as f:
        json.dump({"style_map": STYLE_MAP, "image_size": cfg["image_size"],
                   "style_dim": cfg["style_dim"], "content_dim": cfg["content_dim"]}, f, ensure_ascii=False, indent=2)

    # 写训练日志
    with open(os.path.join(cfg["ckpt_dir"], "train_log.json"), "w") as f:
        json.dump(log, f, indent=2)

    print(f"\n[DONE] 训练完成! 最终模型: {final_dir}")
    print(f"   最佳 G Loss: {best_g:.4f}")


if __name__ == "__main__":
    main()
