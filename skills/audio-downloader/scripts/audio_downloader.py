#!/usr/bin/env python3
"""音频批量下载工具"""
import json
import os
import subprocess
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def get_audio_extension(url: str) -> str:
    audio_exts = ['mp3', 'm4a', 'wav', 'ogg', 'flac', 'aac', 'wma', 'opus']
    match = re.search(r'\.([a-z0-9]+)(?:\?|$|#)', url, re.I)
    if match and match.group(1).lower() in audio_exts:
        return match.group(1).lower()
    return 'mp3'

def generate_dir_name(keyword: str) -> str:
    keyword = sanitize_filename(keyword).replace(' ', '_')
    return f"{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def download_audios(urls: List[Dict], output_dir: str, referer: str, 
                   cookies: Optional[str] = None, delay: float = 0) -> Tuple[Dict, Set[str]]:
    audio_dir = os.path.join(output_dir, "audios")
    os.makedirs(audio_dir, exist_ok=True)
    
    downloaded_urls: Set[str] = set()
    results = {'success': 0, 'fail': 0, 'skip': 0, 'total': len(urls)}
    
    for item in urls:
        url = item['url']
        
        if url in downloaded_urls:
            results['skip'] += 1
            print(f"跳过重复：{item.get('name', url[:50])}")
            if delay > 0: time.sleep(delay)
            continue
        
        name = sanitize_filename(item.get('name', f"audio_{item['index']}"))
        ext = get_audio_extension(url)
        filename = f"{item['index']:03d}_{name}.{ext}"
        filepath = os.path.join(audio_dir, filename)
        
        cmd = ['curl', '-sL', '--referer', referer]
        if cookies: cmd.extend(['-H', f'Cookie: {cookies}'])
        cmd.extend(['-o', filepath, url])
        
        print(f"[{item['index']:3d}/{len(urls)}] 下载：{name}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0 and os.path.getsize(filepath) > 0:
                results['success'] += 1
                downloaded_urls.add(url)
                print(f"      ✓ 成功 ({os.path.getsize(filepath)/1024:.1f} KB)")
            else:
                results['fail'] += 1
                print(f"      ✗ 失败")
        except subprocess.TimeoutExpired:
            results['fail'] += 1
            print(f"      ✗ 超时")
        except Exception as e:
            results['fail'] += 1
            print(f"      ✗ 错误：{e}")
        
        if delay > 0: time.sleep(delay)
    
    return results, downloaded_urls

def generate_report(urls: List[Dict], downloaded_urls: Set[str], output_dir: str) -> str:
    url_groups = {}
    for item in urls:
        url_groups.setdefault(item['url'], []).append(item)
    
    duplicates = {k: v for k, v in url_groups.items() if len(v) > 1}
    
    report = f"""# 音频下载报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计摘要

| 项目 | 数量 |
|------|------|
| 总音频项 | {len(urls)} |
| 独特音频 | {len(url_groups)} |
| 下载成功 | {len(downloaded_urls)} |
"""
    
    with open(os.path.join(output_dir, 'download_report.md'), 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report

def load_urls(input_file: str) -> List[Dict]:
    with open(input_file, 'r', encoding='utf-8') as f:
        return json.load(f).get('urls', [])

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='音频批量下载工具')
    parser.add_argument('url_file', help='URL JSON 文件路径')
    parser.add_argument('-k', '--keyword', required=True, help='关键词')
    parser.add_argument('-r', '--referer', required=True, help='Referer URL')
    parser.add_argument('-c', '--cookies', help='Cookie 字符串')
    parser.add_argument('-d', '--delay', type=float, default=0, help='下载间隔（秒）')
    
    args = parser.parse_args()
    
    output_dir = generate_dir_name(args.keyword)
    urls = load_urls(args.url_file)
    results, downloaded = download_audios(urls, output_dir, args.referer, args.cookies, args.delay)
    generate_report(urls, downloaded, output_dir)
    
    print(f"\n完成！成功：{results['success']}, 失败：{results['fail']}, 跳过：{results['skip']}")
    print(f"输出目录：{os.path.abspath(output_dir)}")