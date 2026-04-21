#!/usr/bin/env python3
"""
图片URL解析器 - 从缓存的HTML中查找角色图片
用法: python parse_images.py <剧集名> <关键词> [输出目录]
示例:
  python parse_images.py 逐玉 樊长玉
  python parse_images.py 逐玉 谢征 言正
  python parse_images.py 逐玉 鬼灭之刃 灶门炭治郎
  python parse_images.py 逐玉 炭治郎 /Users/lk/vibe_projects/x_test
"""

import os
import sys
import json
import re
from bs4 import BeautifulSoup

def try_import_jieba():
    """尝试导入jieba，如果失败返回None"""
    try:
        import jieba
        return jieba
    except ImportError:
        return None

def smart_tokenize(input_str):
    """
    智能分词策略：
    1. 首先尝试用常见分隔符分割（顿号、逗号、空格）
    2. 提取末尾的2-4个字作为关键词
    3. 如果jieba可用，使用jieba分词
    """
    keywords = []
    
    separators = re.compile(r'[、，,\s]+')
    parts = separators.split(input_str)
    parts = [p.strip() for p in parts if p.strip()]
    
    for part in parts:
        if len(part) <= 4:
            keywords.append(part)
        else:
            end_part = part[-4:]
            keywords.append(end_part)
            if len(part) > 4:
                end_part_2 = part[-2:]
                if end_part_2 not in keywords:
                    keywords.append(end_part_2)
            start_part = part[:2]
            if start_part not in keywords:
                keywords.append(start_part)
    
    jieba = try_import_jieba()
    if jieba and len(keywords) == 1 and len(keywords[0]) > 4:
        words = jieba.cut(keywords[0])
        for w in words:
            if len(w) >= 2:
                keywords.append(w)
    
    unique_keywords = []
    seen = set()
    for kw in keywords:
        if kw not in seen:
            unique_keywords.append(kw)
            seen.add(kw)
    
    return unique_keywords

def find_images_by_keywords(html, keywords, filter_word="饰演"):
    """
    在HTML中查找包含关键词的图片
    keywords: 关键词列表
    filter_word: 过滤词
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

        alt_text = img.get('alt', '')
        
        if alt_text and filter_word in alt_text:
            alt_without_filter = alt_text.replace(filter_word, '').replace('（', '').replace('）', '').replace('(', '').replace(')', '')
            match_count = 0
            for kw in keywords:
                if kw in alt_without_filter:
                    match_count += 1
            
            if match_count > 0:
                results.append({
                    'img_url': img_src,
                    'context': alt_text,
                    'match_count': match_count,
                    'context_len': len(alt_text)
                })

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
    cache_subdir = tmp_dir

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
    """更新角色数据文件中的imageUrl"""
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
        data['characters'][character_name]['imageUrl'] = image_url
        if 'imagePath' in data['characters'][character_name]:
            del data['characters'][character_name]['imagePath']
        updated = True
        print(f"已更新 {character_name} 的 imageUrl")

    for char_key, char_data in data.get('characters', {}).items():
        if char_key == character_name:
            continue
        if character_name in str(char_data):
            if isinstance(char_data, dict):
                char_data['imageUrl'] = image_url
                if 'imagePath' in char_data:
                    del char_data['imagePath']
                updated = True

    if updated:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存到: {data_file}")
        return True

    print(f"未找到角色: {character_name}")
    return False

def main():
    if len(sys.argv) < 3:
        print("用法: python parse_images.py <剧集名> <关键词> [输出目录]")
        print("示例:")
        print("  python parse_images.py 逐玉 樊长玉")
        print("  python parse_images.py 逐玉 谢征 言正")
        print("  python parse_images.py 逐玉 鬼灭之刃 灶门炭治郎")
        print("  python parse_images.py 逐玉 炭治郎")
        print("  python parse_images.py 逐玉 灶门 /Users/lk/vibe_projects/x_test")
        sys.exit(1)

    drama = sys.argv[1]
    keyword_str = sys.argv[2]
    
    project_root = None
    if len(sys.argv) >= 4:
        project_root = sys.argv[3]

    keywords = smart_tokenize(keyword_str)

    filter_word = "饰演"
    if "饰演" in keywords:
        keywords.remove("饰演")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if project_root:
        tmp_dir = os.path.join(project_root, drama, "tmp")
    else:
        tmp_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "..", "tmp"))

    print("=" * 50)
    print(f"剧集: {drama}")
    print(f"分词结果: {keywords}")
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
