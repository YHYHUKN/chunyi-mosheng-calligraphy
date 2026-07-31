# -*- coding: utf-8 -*-
"""快速测试书法网站可达性"""
import requests, urllib3, sys, io
urllib3.disable_warnings()
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

test_urls = [
    ('shufadict.com', 'https://www.shufadict.com/'),
    ('zshufa.com', 'https://www.zshufa.com/'),
    ('ishufa.com', 'https://www.ishufa.com/'),
    ('shufa.e118.cn', 'https://shufa.e118.cn/'),
    ('yingbishufa.com', 'https://www.yingbishufa.com/'),
]

for name, url in test_urls:
    try:
        r = requests.get(url, headers=headers, timeout=8, verify=False)
        print(f'{name}: {r.status_code} ({len(r.text)} bytes)')
        if r.status_code == 200 and len(r.text) > 3000:
            soup = BeautifulSoup(r.text, 'lxml')
            for a in soup.find_all('a', href=True)[:5]:
                t = a.get_text(strip=True)
                if t and len(t) < 15:
                    href = a['href'][:80]
                    print(f'  {t} -> {href}')
    except Exception as e:
        print(f'{name}: FAIL - {type(e).__name__}')
