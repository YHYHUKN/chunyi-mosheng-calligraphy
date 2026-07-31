# -*- coding: utf-8 -*-
"""测试 Bing/DuckDuckGo 图片搜索"""
import requests, urllib3, sys, io, re
urllib3.disable_warnings()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

query = '%E7%B1%B3%E8%8A%BE+%E8%A1%8C%E4%B9%A6+%E5%AD%97%E5%B8%96'
url = f'https://www.bing.com/images/search?q={query}&first=1&count=30&qft=+filterui:photo-photo'

r = requests.get(url, headers=headers, timeout=10, verify=False)
print('Bing Status:', r.status_code, 'Length:', len(r.text))

# Bing 图片搜索的 murl 格式
img_urls = re.findall(r'murl&quot;:&quot;(https?://[^&]+)&quot;', r.text)
if not img_urls:
    img_urls = re.findall(r'"murl":"(https?://[^"]+)"', r.text)
if not img_urls:
    # 尝试其他模式
    img_urls = re.findall(r'(https?://[^"\s]+?\.(?:jpg|jpeg|png))', r.text)

print(f'Found {len(img_urls)} image URLs')
for u in img_urls[:10]:
    print(f'  {u[:120]}')
