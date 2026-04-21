#!/usr/bin/env python3
"""
网页缓存爬虫 - 只负责将网页内容保存到tmp目录
用法: python scrape.py <剧集名> <URL> [输出目录]
示例: 
  python scrape.py 逐玉 https://movie.douban.com/subject/36554061/celebrities
  python scrape.py 逐玉 https://www.tvmao.com/kanju/ZGFqI2Fi/actors
  python scrape.py 逐玉 https://www.tvmao.com/kanju/ZGFqI2Fi/actors /Users/lk/vibe_projects/x_test
"""

import os
import sys
import requests
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

def fetch(url):
    """获取页面"""
    print(f"访问: {url}")
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        resp = session.get(url, timeout=30, allow_redirects=True)
        
        if resp.url != url and 'login' in resp.url.lower():
            print(f"需要登录: {resp.url}")
            return None
            
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"失败: {e}")
        return None

def save_cache(html, cache_file):
    """保存到缓存文件"""
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"已缓存到: {cache_file}")

def main():
    if len(sys.argv) < 3:
        print("用法: python scrape.py <剧集名> <URL> [输出目录]")
        print("示例:")
        print("  python scrape.py 逐玉 https://movie.douban.com/subject/36554061/celebrities")
        print("  python scrape.py 逐玉 https://www.tvmao.com/kanju/ZGFqI2Fi/actors")
        print("  python scrape.py 逐玉 https://www.tvmao.com/kanju/ZGFqI2Fi/actors /Users/lk/vibe_projects/x_test")
        sys.exit(1)
    
    drama = sys.argv[1]
    url = sys.argv[2]
    
    project_root = None
    if len(sys.argv) >= 4:
        project_root = sys.argv[3]
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if project_root:
        drama_dir = os.path.join(project_root, drama)
    else:
        drama_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", drama))
    
    tmp_dir = os.path.join(drama_dir, "tmp")
    
    parsed = urlparse(url)
    filename = parsed.netloc + parsed.path.replace('/', '_') + '.html'
    filename = filename[:100]
    
    cache_file = os.path.join(tmp_dir, filename)
    
    print("=" * 50)
    print(f"剧集: {drama}")
    print(f"URL: {url}")
    print(f"输出: {drama_dir}")
    print(f"缓存: {cache_file}")
    print("=" * 50)
    
    html = fetch(url)
    if not html:
        print("获取页面失败")
        sys.exit(1)
    
    save_cache(html, cache_file)
    
    print("=" * 50)
    print("完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
