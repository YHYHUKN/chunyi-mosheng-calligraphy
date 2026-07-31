import sys, json
sys.stdout.reconfigure(encoding='utf-8')
try:
    with open(r'd:\书法春\checkpoints\train_log.json', 'r', encoding='utf-8') as f:
        logs = json.load(f)
    print(f"共 {len(logs)} 条日志")
    print("最后10个epoch:")
    for ep in logs[-10:]:
        print(f'  Epoch {ep["epoch"]:3d}: G_loss={ep["g_loss"]:.4f}, D_loss={ep["d_loss"]:.4f}')
except Exception as e:
    print(f'Error: {e}')
    import os
    for f in os.listdir(r'd:\书法春\checkpoints'):
        print(f)
