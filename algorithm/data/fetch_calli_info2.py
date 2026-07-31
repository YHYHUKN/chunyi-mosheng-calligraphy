# -*- coding: utf-8 -*-
"""从ModelScope数据集页面提取嵌入数据（用更完整的请求头）"""
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
print(f"HTML长度: {len(html)}")

# 查找所有script标签中的内容
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"找到 {len(scripts)} 个script标签")

for i, script in enumerate(scripts):
    if '__detail_data__' in script or '__APP_DATA__' in script or len(script) > 500:
        print(f"\n--- Script #{i} (长度 {len(script)}) ---")
        print(script[:2000])
