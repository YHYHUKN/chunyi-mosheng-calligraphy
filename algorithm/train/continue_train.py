"""
继续训练脚本 - 从 checkpoint 恢复
用法: python algorithm/train/continue_train.py
"""
import os, sys, time, json, glob
from pathlib import Path

TRAIN_DIR   = Path(__file__).resolve().parent
ALGO_DIR    = TRAIN_DIR.parent
PROJECT_DIR = ALGO_DIR.parent
sys.path.insert(0, str(ALGO_DIR))

import torch
from torch.utils.data import DataLoader
from run_train import CalligraphyDS, Trainer, STYLE_MAP, NUM_STYLES, CONFIG

# ---- 配置（覆盖继续训练参数）----
CONTINUE_CFG = {
    "data_root"    : str(ALGO_DIR / "data"),
    "cache_dir"    : str(ALGO_DIR / "data" / ".skeleton_cache"),
    "ckpt_dir"     : str(PROJECT_DIR / "checkpoints"),
    "image_size"   : 128,
    "style_dim"    : 128,
    "content_dim"  : 256,
    "batch_size"   : 4,
    "num_epochs"   : 160,      # 再训160 epoch（总共220）
    "lr_g"         : 5e-5,     # 降低学习率，更精细
    "lr_d"         : 1e-4,     # 降低学习率，防止D过强
    "save_every"   : 20,
    "device"       : "cuda" if torch.cuda.is_available() else "cpu",
    "aug_factor"   : 5,        # 更多增强
}


def find_best_ckpt(ckpt_dir):
    """找到 best checkpoint"""
    ckpts = glob.glob(os.path.join(ckpt_dir, "*_best.pth"))
    if not ckpts:
        # 找最新的 checkpoint
        ckpts = glob.glob(os.path.join(ckpt_dir, "checkpoint_epoch_*.pth"))
    if not ckpts:
        return None
    # 按 epoch 数字排序取最大
    ckpts.sort(key=lambda p: int(''.join(filter(str.isdigit, os.path.basename(p)))))
    return ckpts[-1]


def main():
    cfg = CONTINUE_CFG
    ckpt_path = find_best_ckpt(cfg["ckpt_dir"])

    if not ckpt_path:
        print("[ERROR] 找不到 checkpoint！请先完成初始训练。")
        return

    start_epoch = int(''.join(filter(str.isdigit, os.path.basename(ckpt_path))))
    print(f"[恢复] 从 {ckpt_path} 继续训练（已完成 {start_epoch} epoch）")

    # ---- 数据集 ----
    print("\n[1/3] 加载数据集...")
    ds = CalligraphyDS(
        data_root  = cfg["data_root"],
        cache_dir  = cfg["cache_dir"],
        image_size = cfg["image_size"],
        aug_factor = cfg["aug_factor"],
        style_map  = STYLE_MAP,
    )
    loader = DataLoader(ds, batch_size=cfg["batch_size"],
                        shuffle=True, num_workers=0, drop_last=True)
    print(f"  DataLoader: {len(ds)} 样本 → {len(loader)} batches/epoch")

    # ---- 模型 + 加载权重 ----
    print("\n[2/3] 初始化模型并加载权重...")
    trainer = Trainer(cfg)
    ckpt = torch.load(ckpt_path, map_location="cpu")
    trainer.style_enc.load_state_dict(ckpt["style_encoder"])
    trainer.content_enc.load_state_dict(ckpt["content_encoder"])
    trainer.gen.load_state_dict(ckpt["generator"])
    trainer.disc.load_state_dict(ckpt["discriminator"])
    # 用新的低学习率
    trainer.opt_g = torch.optim.Adam(
        list(trainer.gen.parameters()) +
        list(trainer.style_enc.parameters()) +
        list(trainer.content_enc.parameters()),
        lr=cfg["lr_g"], betas=(0.5, 0.999))
    trainer.opt_d = torch.optim.Adam(
        trainer.disc.parameters(), lr=cfg["lr_d"], betas=(0.5, 0.999))
    trainer.sch_g = torch.optim.lr_scheduler.CosineAnnealingLR(
        trainer.opt_g, T_max=cfg["num_epochs"] - start_epoch)
    trainer.sch_d = torch.optim.lr_scheduler.CosineAnnealingLR(
        trainer.opt_d, T_max=cfg["num_epochs"] - start_epoch)
    print("  权重加载成功，学习率已降低")

    # ---- 继续训练 ----
    remaining = cfg["num_epochs"] - start_epoch
    print(f"\n[3/3] 继续训练 {remaining} epochs (epoch {start_epoch+1} → {cfg['num_epochs']})...")
    print(f"  lr_g={cfg['lr_g']}  lr_d={cfg['lr_d']}")

    log = []
    best_g = float("inf")

    for epoch in range(start_epoch + 1, cfg["num_epochs"] + 1):
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
    with open(os.path.join(final_dir, "style_map.json"), "w", encoding="utf-8") as f:
        json.dump({"style_map": STYLE_MAP, "image_size": cfg["image_size"],
                   "style_dim": cfg["style_dim"], "content_dim": cfg["content_dim"]}, f, ensure_ascii=False, indent=2)

    print(f"\n[DONE] 继续训练完成! 最终模型: {final_dir}")
    print(f"   最佳 G Loss: {best_g:.4f}")


if __name__ == "__main__":
    main()
