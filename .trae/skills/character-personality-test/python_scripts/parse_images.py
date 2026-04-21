#!/usr/bin/env python3
"""
图片URL解析器 - 从缓存的HTML中查找角色图片
用法: python parse_images.py <剧集名> <关键词1> [关键词2] ...
示例:
  python parse_images.py 逐玉 樊长玉
  python parse_images.py 逐玉 谢征 言正
  python parse_images.py 逐玉 谢征
"""

import os
import sys
import json
import re
from bs4 import BeautifulSoup

def find_images_by_keywords(html, keywords, filter_word="饰演"):
    """
    在HTML中查找包含关键词的图片
    keywords: 关键词列表，如 ["谢征", "言正"]
    filter_word: 过滤词，如"饰演"，包含此词的结果将被排除
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for img in soup.find_all('img'):
        img_src = img.get('src') or img.get('data-src') or ""
        if not img_src:
            continue
        if 'default' in img_src.lower() or 'logo' in img_src.lower() or 'icon' in img_src.lower():
            continue
        if not img_src.startswith('http'):
            if img_src.startswith('//'):
                img_src = 'https:' + img_src

        context = ""
        try:
            parent = img.parent
            if parent:
                context = parent.get_text(strip=True)
                if len(context) < 2:
                    for _ in range(3):
                        prev = parent.find_previous_sibling()
                        if prev:
                            context = prev.get_text(strip=True) + context
                            parent = prev
                        else:
                            break
        except:
            pass

        if filter_word and filter_word in context:
            continue

        match_count = 0
        for kw in keywords:
            if kw in context:
                match_count += 1

        if match_count > 0:
            results.append({
                'img_url': img_src,
                'context': context,
                'match_count': match_count,
                'context_len': len(context)
            })

    results.sort(key=lambda x: (-x['match_count'], x['context_len']))

    if results:
        return results[0]['img_url']

    return None

def find_image_in_cache(drama, keywords, tmp_dir, filter_word="饰演"):
    """在缓存目录中查找角色图片"""
    cache_subdir = os.path.join(tmp_dir, drama)

    if not os.path.exists(cache_subdir):
        print(f"缓存目录不存在: {cache_subdir}")
        print(f"请先运行: python scrape.py {drama} <URL>")
        return None

    html_files = []
    for root, dirs, files in os.walk(cache_subdir):
        for f in files:
            if f.endswith('.html'):
                if 'tvmao' in f.lower():
                    html_files.append(os.path.join(root, f))

    if not html_files:
        for root, dirs, files in os.walk(cache_subdir):
            for f in files:
                if f.endswith('.html'):
                    html_files.append(os.path.join(root, f))

    if not html_files:
        print(f"未找到缓存文件: {cache_subdir}")
        return None

    print(f"关键词: {keywords}")
    print(f"过滤词: {filter_word}")
    print(f"搜索 {len(html_files)} 个缓存文件...")

    for html_file in sorted(html_files):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html = f.read()
        except:
            continue

        img_url = find_images_by_keywords(html, keywords, filter_word)
        if img_url:
            print(f"在 {os.path.basename(html_file)} 中找到图片")
            return img_url

    return None

def update_character_image(drama, character_name, image_url):
    """更新角色数据文件中的imagePath"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", drama, "data", "questions.json"))

    if not os.path.exists(data_file):
        print(f"数据文件不存在: {data_file}")
        return False

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        return False
    except Exception as e:
        print(f"读取文件失败: {e}")
        return False

    updated = False

    if character_name in data.get('characters', {}):
        data['characters'][character_name]['imagePath'] = image_url
        data['characters'][character_name]['imageUrl'] = image_url
        updated = True
        print(f"已更新 {character_name} 的 imagePath")

    for char_key, char_data in data.get('characters', {}).items():
        if char_key == character_name:
            continue
        if character_name in str(char_data):
            if isinstance(char_data, dict):
                char_data['imagePath'] = image_url
                char_data['imageUrl'] = image_url
                updated = True

    if updated:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存到: {data_file}")
        return True

    print(f"未找到角色: {character_name}")
    return False

def parse_keywords(input_str):
    """解析输入的关键词，支持顿号、分号、逗号分隔"""
    keywords = re.split(r'[、，,\s]+', input_str)
    keywords = [kw.strip() for kw in keywords if kw.strip()]
    return keywords

def main():
    if len(sys.argv) < 3:
        print("用法: python parse_images.py <剧集名> <关键词1> [关键词2] ...")
        print("示例:")
        print("  python parse_images.py 逐玉 樊长玉")
        print("  python parse_images.py 逐玉 谢征 言正")
        print("  python parse_images.py 逐玉 谢征 饰演")
        sys.exit(1)

    drama = sys.argv[1]
    keyword_str = sys.argv[2]

    keywords = parse_keywords(keyword_str)

    filter_word = "饰演"
    if "饰演" in keywords:
        keywords.remove("饰演")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "tmp"))

    print("=" * 50)
    print(f"剧集: {drama}")
    print("=" * 50)

    img_url = find_image_in_cache(drama, keywords, tmp_dir, filter_word)

    if not img_url:
        print("未找到图片URL")
        sys.exit(1)

    print(f"图片URL: {img_url}")

    update_character_image(drama, keywords[0], img_url)

    print("=" * 50)
    print("完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()
