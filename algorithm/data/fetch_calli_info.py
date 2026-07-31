# -*- coding: utf-8 -*-
"""从ModelScope网页提取云墨济心数据集的文件列表"""
import sys, json, re
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://www.modelscope.cn/datasets/CalliTongji/Calli-Tongji_A_Dataset_of_Historical_Calligraphy_Styles'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
resp = urllib.request.urlopen(req, timeout=30)
html = resp.read().decode('utf-8', errors='replace')

print(f"HTML长度: {len(html)}")

# 提取 __detail_data__
m = re.search(r'window\.__detail_data__\s*=\s*(\{.*?\});\s*</script>', html, re.DOTALL)
if m:
    raw = m.group(1)
    data = json.loads(raw)
    
    print("\n=== 基本信息 ===")
    keys = list(data.keys())
    print(f"顶层字段: {keys}")
    
    for key in ['Name', 'Namespace', 'Path', 'Githash', 'StorageSize', 'DownloadCount']:
        print(f"  {key}: {data.get(key, '?')}")
    
    # Readme
    readme = data.get('Readme', '')
    if readme:
        print(f"\n=== README (前1000字) ===")
        print(readme[:1000])
    
    # Tree/Files
    tree = data.get('Tree', [])
    if not tree:
        tree = data.get('Files', [])
    if not tree:
        # 搜索所有可能的文件列表字段
        for k, v in data.items():
            if isinstance(v, list) and len(v) > 0:
                if isinstance(v[0], dict):
                    print(f"\n列表字段 '{k}': {len(v)} 项")
                    print(f"  第一项keys: {list(v[0].keys())}")
                    print(f"  第一项: {json.dumps(v[0], ensure_ascii=False)[:200]}")
    
    print(f"\nTree数量: {len(tree)}")
    for item in tree[:80]:
        tp = item.get('Type', item.get('type', '?'))
        nm = item.get('Name', item.get('name', '?'))
        sz = item.get('Size', item.get('size', 0))
        print(f"  [{tp}] {nm}  ({sz} bytes)")
else:
    print("未找到 __detail_data__")
    # 尝试其他模式
    for pat in [r'window\.(\w+)\s*=\s*(\{.*?\});\s*</script>']:
        matches = re.findall(pat, html, re.DOTALL)
        for name, raw in matches:
            if len(raw) > 100:
                print(f"\n找到 window.{name}, 长度: {len(raw)}")
                print(raw[:300])
