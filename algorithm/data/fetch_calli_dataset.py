# -*- coding: utf-8 -*-
"""直接下载 dataset.txt 查看50个开源类别"""
import sys, json, re
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

# 下载 dataset.txt
url = 'https://www.modelscope.cn/api/v1/datasets/CalliTongji/Calli-Tongji_A_Dataset_of_Historical_Calligraphy_Styles/repo/files?Revision=master&Path=dataset.txt&PageSize=1&PageNumber=1'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/json',
})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    text = resp.read().decode('utf-8')
    print("API响应:")
    print(text[:2000])
except Exception as e:
    print(f"API失败: {e}")

# 直接下载文件
print("\n尝试直接下载dataset.txt...")
for path in ['dataset.txt', 'master/dataset.txt']:
    furl = f'https://www.modelscope.cn/datasets/CalliTongji/Calli-Tongji_A_Dataset_of_Historical_Calligraphy_Styles/resolve/master/{path}'
    try:
        req2 = urllib.request.Request(furl, headers={'User-Agent': 'Mozilla/5.0'})
        resp2 = urllib.request.urlopen(req2, timeout=30)
        content = resp2.read().decode('utf-8')
        print(f"\n=== {path} ({len(content)} bytes) ===")
        print(content[:5000])
        
        # 保存
        with open('d:/书法春/algorithm/data/calli_dataset.txt', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n已保存!")
        break
    except Exception as e:
        print(f"  {path}: {e}")
