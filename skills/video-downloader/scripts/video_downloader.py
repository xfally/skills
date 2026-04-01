#!/usr/bin/env python
"""
Video Downloader Skill v0.0.1
Download and transcode videos to PPT-compatible formats

URL Acquisition Methods:
1. Browser Automation Tools - Extract URLs using browser automation tools (headless mode recommended)
2. User-provided - Users directly provide video URLs

This script handles downloading and transcoding only, not searching.
"""

import os
import re
import sys
import json
import argparse
import subprocess
import shutil
from datetime import datetime


def check_dependencies() -> dict:
    """
    Check if required dependencies are installed.
    Returns dict with 'installed' list and 'missing' list.
    """
    dependencies = {
        "yt-dlp": {"check_cmd": ["yt-dlp", "--version"], "purpose": "Downloading"},
        "ffmpeg": {"check_cmd": ["ffmpeg", "-version"], "purpose": "Transcoding"},
        "ffprobe": {"check_cmd": ["ffprobe", "-version"], "purpose": "Codec detection"},
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

        if tool == "yt-dlp":
            print("   Install with:")
            print("     macOS/Linux: pip install yt-dlp")
            print("     macOS:       brew install yt-dlp")
            print("     Windows:     pip install yt-dlp")

        elif tool == "ffmpeg":
            print("   Install with:")
            print("     macOS:       brew install ffmpeg")
            print("     Linux:       sudo apt install ffmpeg (Debian/Ubuntu)")
            print("     Linux:       sudo dnf install ffmpeg (Fedora)")
            print("     Windows:     winget install ffmpeg (from gyan.dev)")
            print("                  Alternative: https://www.gyan.dev/ffmpeg/builds/")

        elif tool == "ffprobe":
            print("   Note: ffprobe is included with ffmpeg")
            print("   Install ffmpeg using the instructions above")

    print("\n" + "=" * 60)
    print("Please install missing dependencies and try again.")
    print("=" * 60)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Download videos and intelligently transcode them to PPT-compatible formats. URLs must be obtained in advance (browser automation tools or user-provided)."
    )

    parser.add_argument("keyword", help="Search keyword")
    parser.add_argument(
        "--count", type=int, default=3, help="Number of videos to download (default: 3)"
    )
    parser.add_argument("--max-duration", type=float, help="Maximum duration (minutes)")
    parser.add_argument("--min-duration", type=float, help="Minimum duration (minutes)")
    parser.add_argument(
        "--quality",
        choices=["4k", "1080p", "720p", "480p"],
        default="720p",
        help="Video quality (default: 720p)",
    )
    parser.add_argument("--platform", help="Specify platform (bilibili/youtube, etc.)")
    parser.add_argument(
        "--output-dir",
        default=os.path.expanduser("~/Downloads/videos"),
        help="Output directory (default: ~/Downloads/videos)",
    )
    parser.add_argument("--urls", nargs="+", help="List of video URLs")
    parser.add_argument(
        "--no-transcode", action="store_true", help="Disable transcoding"
    )
    parser.add_argument(
        "--force-transcode", action="store_true", help="Force transcoding"
    )
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    return parser.parse_args()


def get_quality_resolution(quality: str) -> tuple:
    """Get resolution based on quality parameter"""
    resolution_map = {
        "4k": (3840, 2160),
        "1080p": (1920, 1080),
        "720p": (1280, 720),
        "480p": (854, 480),
    }
    return resolution_map.get(quality, (1920, 1080))


def sanitize_filename(filename: str) -> str:
    """Sanitize illegal characters from filename"""
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, "_")
    # Replace spaces with underscores to prevent issues with shell commands
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[\0-\31]", "", filename)
    if len(filename) > 100:
        filename = filename[:100]
    return filename.strip("._ ")


def get_video_info(url: str) -> dict:
    """Get video information using yt-dlp (no download)"""
    try:
        cmd = ["yt-dlp", "--dump-json", "--no-warnings", "--no-download", url]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        info = json.loads(result.stdout)

        return {
            "url": url,
            "title": info.get("title", "Unknown"),
            "duration": info.get("duration", 0) or 0,
            "platform": info.get("extractor", "unknown"),
            "info": info,
        }
    except Exception as e:
        print(f"   Warning: Failed to get info: {e}")
        return None


def download_video(url_info: dict, output_dir: str, index: int) -> str:
    url = url_info["url"]
    title = url_info["title"]

    os.makedirs(output_dir, exist_ok=True)

    safe_title = sanitize_filename(title)
    output_template = os.path.join(output_dir, f"{index:02d}_{safe_title}.%(ext)s")

    print(f"Downloading #{index}: {title}")
    print(f"   Save location: {output_dir}/{index:02d}_{safe_title}.mp4")

    cmd = [
        "yt-dlp",
        "-o",
        output_template,
        "--no-warnings",
        "--merge-output-format",
        "mp4",
        url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            print(f"Error: Download failed: {result.stderr[:200]}")
            return None

        for ext in ["mp4", "webm", "mkv", "flv"]:
            output_file = os.path.join(output_dir, f"{index:02d}_{safe_title}.{ext}")
            if os.path.exists(output_file):
                print(f"Success: Download completed")
                return output_file

        files = [f for f in os.listdir(output_dir) if f.startswith(f"{index:02d}_")]
        if files:
            output_file = os.path.join(output_dir, sorted(files)[-1])
            print(f"Success: Download completed: {output_file}")
            return output_file

        return None

    except subprocess.TimeoutExpired:
        print(f"Error: Download timed out")
        return None
    except Exception as e:
        print(f"Error: Download error: {e}")
        return None


def check_video_codec(file_path: str) -> dict:
    """Check video codec format"""
    if not os.path.exists(file_path):
        return None

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,r_frame_rate",
        "-of",
        "json",
        file_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)

        if "streams" in info and len(info["streams"]) > 0:
            stream = info["streams"][0]
            return {
                "codec": stream.get("codec_name", "unknown"),
                "width": stream.get("width", 0),
                "height": stream.get("height", 0),
                "fps": stream.get("r_frame_rate", "0/1"),
            }
        return None
    except Exception as e:
        return None


def needs_transcode(codec_info: dict, force: bool = False) -> tuple:
    """
    Determine if transcoding is needed
    Returns: (needs_transcode: bool, reason: str)
    """
    if force:
        return (True, "User forced transcoding")

    if not codec_info:
        return (True, "Unable to detect codec format")

    codec = codec_info.get("codec", "").lower()

    # PPT-compatible codecs
    COMPATIBLE_CODECS = {
        "h264": "H.264/AVC - Fully PPT compatible",
        "avc1": "H.264/AVC - Fully PPT compatible",
        "hevc": "H.265/HEVC - Supported by modern PPT",
        "h265": "H.265/HEVC - Supported by modern PPT",
        "mp4v": "MPEG-4 - PPT compatible",
    }

    # Codecs requiring transcoding
    INCOMPATIBLE_CODECS = {
        "av1": "AV1 - Not supported by PPT, must transcode",
        "vp9": "VP9 - Not supported by PPT, must transcode",
        "vp8": "VP8 - Not supported by PPT, must transcode",
    }

    if codec in COMPATIBLE_CODECS:
        return (False, COMPATIBLE_CODECS.get(codec, "Compatible"))

    if codec in INCOMPATIBLE_CODECS:
        return (True, INCOMPATIBLE_CODECS.get(codec, "Needs transcoding"))

    return (True, f"Unknown codec ({codec}), transcoding recommended for compatibility")


def transcode_video(input_file: str, output_dir: str, quality: str, index: int) -> str:
    """Transcode video to H.264 + AAC + MP4 format"""
    if not os.path.exists(input_file):
        return None

    # Create ppt_compatible subdirectory
    ppt_dir = os.path.join(output_dir, "ppt_compatible")
    os.makedirs(ppt_dir, exist_ok=True)

    base_name = os.path.basename(input_file)
    # Remove original file prefix (e.g., 01_) to avoid duplication
    name_without_ext = os.path.splitext(base_name)[0]
    # Remove numeric prefix at start (e.g., 01_)
    name_clean = re.sub(r"^\d+_", "", name_without_ext)
    # Generate new filename: {index:02d}_{clean_name}.mp4 (no _ppt suffix)
    output_file = os.path.join(ppt_dir, f"{index:02d}_{name_clean}.mp4")

    width, height = get_quality_resolution(quality)

    print(f"Transcoding: {base_name} → {quality} ({width}x{height})")

    cmd = [
        "ffmpeg",
        "-i",
        input_file,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-r",
        "30",
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        "-y",
        output_file,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0 or not os.path.exists(output_file):
            print(f"Error: Transcoding failed")
            return None

        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"Success: Transcoding completed: {output_file} ({file_size:.1f}MB)")
        return output_file

    except Exception as e:
        print(f"Error: Transcoding error: {e}")
        return None


def verify_video(file_path: str) -> dict:
    """Verify video format"""
    if not os.path.exists(file_path):
        return None

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height,r_frame_rate",
        "-of",
        "default=noprint_wrappers=1",
        file_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                info[key] = value
        return info
    except:
        return None


def main():
    dep_check = check_dependencies()
    if dep_check["missing"]:
        print_install_instructions(dep_check["missing"])
        return 1

    args = parse_args()

    print("=" * 60)
    print("Video Downloader Skill v0.0.1")
    print("=" * 60)
    print(f"Keyword: {args.keyword}")
    print(f"Count: {args.count}")
    if args.urls:
        print(f"URL count: {len(args.urls)}")
    print(f"Quality: {args.quality}")
    print(f"Output directory: {os.path.expanduser(args.output_dir)}")
    print("=" * 60)
    print()

    # Determine output directory: {output_dir}/{keyword}_YYYYMMDD_HHMMSS/
    output_base = os.path.expanduser(args.output_dir)
    keyword_dir = sanitize_filename(args.keyword)
    if not keyword_dir:
        keyword_dir = "videos"

    # Add timestamp suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keyword_dir_with_time = f"{keyword_dir}_{timestamp}"

    output_dir = os.path.join(output_base, keyword_dir_with_time)

    print(f"Output directory: {output_dir}")
    print(f"   Base directory: {output_base}")
    print(f"   Keyword directory: {keyword_dir_with_time}")
    print()

    # Prepare URL list
    urls_to_process = []

    if args.urls:
        # Get URLs from command line
        print(f"Using {len(args.urls)} provided URLs")
        for i, url in enumerate(args.urls, 1):
            print(f"  {i}. {url}")
            urls_to_process.append({"url": url, "title": f"video_{i}", "duration": 0})
    else:
        # No URLs provided
        print("Warning: No URLs provided")
        print()
        print("Please obtain URLs using one of the following methods:")
        print()
        print("Method 1: Use browser automation tools (recommended)")
        print(
            "   Use browser automation tools (headless mode recommended) to search and extract URLs"
        )
        search_url = f"https://cn.bing.com/videos/search?q={args.keyword.replace(' ', '+')}+site:bilibili.com"
        print(f"   Search URL: {search_url}")
        print()
        print("Method 2: Provide manually")
        print(
            "   Open the above URL, copy video URLs, and re-run the command with --urls parameter"
        )
        print()
        print("Example command:")
        print(f'   python scripts/video_downloader.py "{args.keyword}" \\')
        print(f"     --urls URL1 URL2 URL3")
        print()
        return 0

    if args.dry_run:
        print("\nDry run completed")
        return 0

    print()
    print("=" * 60)
    print("Step 1: Downloading videos")
    print("=" * 60)

    downloaded_files = []
    for i, url_info in enumerate(urls_to_process[: args.count], 1):
        info = get_video_info(url_info["url"])
        if info:
            url_info = info

        file_path = download_video(url_info, output_dir, i)
        if file_path:
            downloaded_files.append((i, file_path, url_info))
        print()

    if not downloaded_files:
        print("Error: No videos were successfully downloaded")
        return 1

    print("=" * 60)
    print("Download completion statistics")
    print("=" * 60)
    print(f"Successfully downloaded: {len(downloaded_files)} videos")
    print(f"Output directory: {output_dir}")
    print()

    # Intelligent transcoding
    if not args.no_transcode:
        print("=" * 60)
        print("Step 2: Intelligent transcoding detection")
        print("=" * 60)

        transcoded_files = []
        copied_files = []

        for index, input_file, url_info in downloaded_files:
            base_name = os.path.basename(input_file)

            codec_info = check_video_codec(input_file)

            src_codec = "unknown"
            if codec_info:
                src_codec = codec_info.get("codec", "unknown")
                width = codec_info.get("width", 0)
                height = codec_info.get("height", 0)
                print(f"\nVideo: {base_name}")
                print(f"   Codec: {src_codec}, Resolution: {width}x{height}")

            needs, reason = needs_transcode(codec_info, args.force_transcode)
            print(f"   Decision: {reason}")

            if needs:
                output_file = transcode_video(
                    input_file, output_dir, args.quality, index
                )
                if output_file:
                    transcoded_files.append(
                        (index, output_file, src_codec, "h264", url_info)
                    )
            else:
                ppt_dir = os.path.join(output_dir, "ppt_compatible")
                os.makedirs(ppt_dir, exist_ok=True)

                name_without_ext = os.path.splitext(base_name)[0]
                name_clean = re.sub(r"^\d+_", "", name_without_ext)
                output_file = os.path.join(ppt_dir, f"{index:02d}_{name_clean}.mp4")

                try:
                    os.link(input_file, output_file)
                    print(f"   Success: Compatible, hard link created")
                except:
                    import shutil

                    shutil.copy2(input_file, output_file)
                    print(f"   Success: Compatible, file copied")

                copied_files.append((index, output_file, src_codec, url_info))

        # Verify results
        all_ppt_files = transcoded_files + copied_files
        if all_ppt_files:
            print("\n" + "=" * 60)
            print("Transcoding completed - File verification")
            print("=" * 60)

            for item in all_ppt_files:
                index = item[0]
                file_path = item[1]
                info = verify_video(file_path)
                if info:
                    codec = info.get("codec_name", "unknown")
                    width = info.get("width", "?")
                    height = info.get("height", "?")
                    fps = info.get("r_frame_rate", "?")
                    status = (
                        "Transcoded"
                        if len(item) > 3 and item[2] != item[3]
                        else "Compatible"
                    )
                    print(f"  Success [{status}] {os.path.basename(file_path)}")
                    print(
                        f"    Codec: {codec}, Resolution: {width}x{height}, Frame rate: {fps}"
                    )
                print()

        print("=" * 60)
        print("Final statistics")
        print("=" * 60)
        print(f"Original videos: {len(downloaded_files)}")
        print(f"Transcoded videos: {len(transcoded_files)}")
        print(f"Compatible videos: {len(copied_files)}")
        print()
        print(f"Original files directory: {output_dir}")
        print(f"PPT compatible directory: {os.path.join(output_dir, 'ppt_compatible')}")
        print()
        print(
            "Tip: When inserting into PPT, use files from the ppt_compatible directory"
        )

    # Generate download report
    generate_report(
        total_requested=min(args.count, len(urls_to_process)),
        downloaded=downloaded_files,
        transcoded=transcoded_files if not args.no_transcode else [],
        copied=copied_files if not args.no_transcode else [],
        output_dir=output_dir,
        no_transcode=args.no_transcode,
    )

    return 0


def generate_report(
    total_requested: int,
    downloaded: list,
    transcoded: list,
    copied: list,
    output_dir: str,
    no_transcode: bool = False,
):
    report_lines = [
        "# Video Download Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Output Directory**: `{output_dir}`",
        "",
        "## Summary",
        "",
        "| Item | Count |",
        "|------|-------|",
        f"| Total requested | {total_requested} |",
        f"| Successfully downloaded | {len(downloaded)} |",
    ]

    if not no_transcode:
        report_lines.extend(
            [
                f"| Transcoded (AV1/VP9 → H.264) | {len(transcoded)} |",
                f"| Already compatible (copied) | {len(copied)} |",
            ]
        )

    report_lines.extend(
        [
            "",
            "## Video Details",
            "",
            "| # | Title | Platform | Source → Target | Action | URL |",
            "|---|-------|----------|------------------|--------|-----|",
        ]
    )

    transcode_map = {}
    for item in transcoded:
        index, file_path, src_codec, dst_codec, url_info = item
        transcode_map[index] = (src_codec, dst_codec, "Transcoded")
    for item in copied:
        index, file_path, src_codec, url_info = item
        transcode_map[index] = (src_codec, src_codec, "Direct copy")

    for index, file_path, url_info in downloaded:
        title = url_info.get("title", "Unknown")[:30]
        platform = url_info.get("platform", "unknown")
        url = url_info.get("url", "")
        url_short = url[:50] + "..." if len(url) > 50 else url

        if no_transcode:
            codec_info = "—"
            action = "—"
        elif index in transcode_map:
            src, dst, action = transcode_map[index]
            codec_info = f"{src} → {dst}"
        else:
            codec_info = "—"
            action = "—"

        report_lines.append(
            f"| {index} | {title} | {platform} | {codec_info} | {action} | `{url_short}` |"
        )

    # Output Structure
    report_lines.extend(
        [
            "",
            "## Output Structure",
            "",
            "```",
            f"{os.path.basename(output_dir)}/",
            "├── 01_video.mp4              ← Original downloaded file",
            "├── 02_video.mp4",
            "├── download_report.md        ← This report",
            "└── ppt_compatible/           ← Use files here for PPT",
            "    ├── 01_video.mp4",
            "    └── 02_video.mp4",
            "```",
            "",
            "**For PowerPoint insertion, use files from `ppt_compatible/` directory.**",
            "",
            "---",
            "",
            "*Generated by video-downloader skill*",
        ]
    )

    report_content = "\n".join(report_lines)

    report_path = os.path.join(output_dir, "download_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"📄 Report saved: {report_path}")


if __name__ == "__main__":
    sys.exit(main())
