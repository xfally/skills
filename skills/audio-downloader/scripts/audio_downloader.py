#!/usr/bin/env python3
"""Audio batch download tool with deduplication and report generation."""

import json
import os
import subprocess
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple


def check_dependencies() -> dict:
    """
    Check if required dependencies are installed.
    Returns dict with 'installed' list and 'missing' list.
    """
    dependencies = {
        "curl": {"check_cmd": ["curl", "--version"], "purpose": "Downloading"},
    }

    result = {"installed": [], "missing": []}

    for tool, info in dependencies.items():
        try:
            subprocess.run(info["check_cmd"], capture_output=True, timeout=5)
            result["installed"].append(tool)
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            result["missing"].append(tool)

    return result


def print_install_instructions(missing: list):
    print("\n" + "=" * 60)
    print("⚠️  DEPENDENCIES MISSING - INSTALL REQUIRED")
    print("=" * 60)

    for tool in missing:
        print(f"\n❌ {tool} is not installed")

        if tool == "curl":
            print("   Install with:")
            print("     macOS:       brew install curl")
            print("     Linux:       sudo apt install curl (Debian/Ubuntu)")
            print("     Windows:     winget install curl")

    print("\n" + "=" * 60)
    print("Please install missing dependencies and try again.")
    print("=" * 60)


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def get_audio_extension(url: str) -> str:
    audio_exts = ["mp3", "m4a", "wav", "ogg", "flac", "aac", "wma", "opus"]
    match = re.search(r"\.([a-z0-9]+)(?:\?|$|#)", url, re.I)
    if match and match.group(1).lower() in audio_exts:
        return match.group(1).lower()
    return "mp3"


def generate_dir_name(keyword: str, base_dir: str = None) -> str:
    if base_dir is None:
        base_dir = os.path.expanduser("~/Downloads/audios")
    keyword = sanitize_filename(keyword).replace(" ", "_")
    dir_name = f"{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return os.path.join(base_dir, dir_name)


def download_audios(
    urls: List[Dict],
    output_dir: str,
    referer: str,
    cookies: Optional[str] = None,
    delay: float = 0,
) -> Tuple[Dict, Set[str]]:
    os.makedirs(output_dir, exist_ok=True)

    downloaded_urls: Set[str] = set()
    results = {"success": 0, "fail": 0, "skip": 0, "total": len(urls)}

    for item in urls:
        url = item["url"]

        if url in downloaded_urls:
            results["skip"] += 1
            print(f"Skip duplicate: {item.get('name', url[:50])}")
            if delay > 0:
                time.sleep(delay)
            continue

        name = sanitize_filename(item.get("name", f"audio_{item['index']}"))
        ext = get_audio_extension(url)
        filename = f"{item['index']:03d}_{name}.{ext}"
        filepath = os.path.join(output_dir, filename)

        cmd = ["curl", "-sL", "--referer", referer]
        if cookies:
            cmd.extend(["-H", f"Cookie: {cookies}"])
        cmd.extend(["-o", filepath, url])

        print(f"[{item['index']:3d}/{len(urls)}] Downloading: {name}")

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0 and os.path.getsize(filepath) > 0:
                results["success"] += 1
                downloaded_urls.add(url)
                print(f"      ✓ Success ({os.path.getsize(filepath) / 1024:.1f} KB)")
            else:
                results["fail"] += 1
                print(f"      ✗ Failed")
        except subprocess.TimeoutExpired:
            results["fail"] += 1
            print(f"      ✗ Timeout")
        except Exception as e:
            results["fail"] += 1
            print(f"      ✗ Error: {e}")

        if delay > 0:
            time.sleep(delay)

    return results, downloaded_urls


def generate_report(
    urls: List[Dict],
    downloaded_urls: Set[str],
    output_dir: str,
    results: Dict,
) -> str:
    url_groups = {}
    for item in urls:
        url_groups.setdefault(item["url"], []).append(item)

    report_lines = [
        "# Audio Download Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
        "| Item | Count |",
        "|------|-------|",
        f"| Total audio items | {len(urls)} |",
        f"| Unique audio files | {len(url_groups)} |",
        f"| Successfully downloaded | {results['success']} |",
        f"| Failed | {results['fail']} |",
        f"| Skipped (duplicates) | {results['skip']} |",
        "",
        "## Output Structure",
        "",
        "```",
        f"{os.path.basename(output_dir)}/",
        "├── 001_audio_name.mp3",
        "├── 002_audio_name.m4a",
        "└── download_report.md",
        "```",
        "",
        "---",
        "",
        "*Generated by audio-downloader skill*",
    ]

    report_content = "\n".join(report_lines)

    with open(
        os.path.join(output_dir, "download_report.md"), "w", encoding="utf-8"
    ) as f:
        f.write(report_content)

    return report_content


def load_urls(input_file: str) -> List[Dict]:
    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f).get("urls", [])


if __name__ == "__main__":
    dep_check = check_dependencies()
    if dep_check["missing"]:
        print_install_instructions(dep_check["missing"])
        exit(1)

    import argparse

    parser = argparse.ArgumentParser(description="Audio batch download tool")
    parser.add_argument("url_file", help="URL JSON file path")
    parser.add_argument(
        "-k", "--keyword", required=True, help="Keyword (for folder name)"
    )
    parser.add_argument("-r", "--referer", required=True, help="Referer URL")
    parser.add_argument("-c", "--cookies", help="Cookie string")
    parser.add_argument(
        "-d", "--delay", type=float, default=0, help="Download delay (seconds)"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=os.path.expanduser("~/Downloads/audios"),
        help="Output directory (default: ~/Downloads/audios)",
    )

    args = parser.parse_args()

    output_dir = generate_dir_name(args.keyword, args.output_dir)
    urls = load_urls(args.url_file)
    results, downloaded = download_audios(
        urls, output_dir, args.referer, args.cookies, args.delay
    )
    generate_report(urls, downloaded, output_dir, results)

    print(
        f"\n✅ Done! Success: {results['success']}, Fail: {results['fail']}, Skip: {results['skip']}"
    )
    print(f"📁 Output: {os.path.abspath(output_dir)}")
