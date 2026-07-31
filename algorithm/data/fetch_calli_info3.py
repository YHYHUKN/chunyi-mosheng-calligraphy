# -*- coding: utf-8 -*-
"""从ModelScope页面提取完整数据集信息"""
import sys, json, re
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://www.modelscope.cn/datasets/CalliTongji/Calli-Tongji_A_Dataset_of_Historical_Calligraphy_Styles'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
})
resp = urllib.request.urlopen(req, timeout=30)
html = resp.read().decode('utf-8', errors='replace')

# 提取 __detail_data__
m = re.search(r'window\.__detail_data__\s*=\s*"(.+?)";', html, re.DOTALL)
if not m:
    print("ERROR: 未找到数据")
    sys.exit(1)

raw_json = m.group(1)
# 处理JSON转义
data = json.loads(raw_json)

# 输出基本信息
print("=== 基本信息 ===")
print(f"名称: {data.get('ChineseName')}")
print(f"下载次数: {data.get('Downloads')}")
print(f"许可: {data.get('License')}")

# Tree文件列表
tree = data.get('Tree', [])
print(f"\n=== 文件列表 (共{len(tree)}项) ===")
for item in tree:
    tp = item.get('Type', '?')
    nm = item.get('Name', '?')
    sz = item.get('Size', 0)
    if tp == 'tree':  # 目录
        print(f"  [DIR]  {nm}/")
    else:
        print(f"  [FILE] {nm}  ({sz} bytes)")

# README完整内容
readme = data.get('ReadmeContent', '')
print(f"\n=== README 完整内容 ===")
print(readme)

# 保存到文件
with open('d:/书法春/algorithm/data/calli_tongji_info.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n已保存到 calli_tongji_info.json")
