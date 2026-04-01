---
name: video-downloader
description: >
  Use this skill whenever the user wants to download, save, or extract videos from public platforms.
  Trigger phrases: "download video", "save video", "get video", "视频下载", "下载视频", "保存视频",
  "提取视频", "Bilibili", "YouTube", "抖音", "TikTok", "微博视频", "extract video from URL",
  "视频转码", "convert video format", "make video PPT-compatible", "视频插入PPT".
  Two ways to get video URLs:
  1) The agent uses browser automation tools to extract URLs.
  2) The user provides URLs directly.
  Then download and intelligently transcode to PPT-compatible formats (H.264/MP4).
  Note: This skill does NOT support sites requiring login. Use yt-dlp directly with --cookies-from-browser for authenticated downloads.
---

# Video Downloader Skill

Download videos from public platforms and intelligently transcode them into PPT-compatible formats.

**Limitation:** This skill does NOT support sites requiring login. For authenticated downloads, use `yt-dlp --cookies-from-browser` directly.

---

## Step 0: Check Dependencies (CRITICAL)

**Before downloading any videos, you MUST verify all dependencies are installed.**

This skill requires `yt-dlp`, `ffmpeg`, and `ffprobe`. Missing dependencies will cause partial failures mid-task.

### Check Commands

```bash
yt-dlp --version
ffmpeg -version
ffprobe -version
```

**Expected output:**
- `yt-dlp --version` → prints version number (e.g., "2025.03.31")
- `ffmpeg -version` → prints version info with build configuration
- `ffprobe -version` → prints version info (same as ffmpeg)

### If Dependencies Are Missing

**Install yt-dlp:**

| Platform    | Install Command                               |
| ----------- | --------------------------------------------- |
| macOS/Linux | `pip install yt-dlp` or `brew install yt-dlp` |
| Windows     | `pip install yt-dlp`                          |

**Install ffmpeg (includes ffprobe):**

| Platform | Install Method                                      |
| -------- | --------------------------------------------------- |
| macOS    | `brew install ffmpeg`                               |
| Linux    | `sudo apt install ffmpeg` (Debian/Ubuntu)           |
|          | `sudo dnf install ffmpeg` (Fedora)                  |
| Windows  | `winget install ffmpeg` (from gyan.dev builds)      |
|          | Alternative: https://www.gyan.dev/ffmpeg/builds/    |

**Windows users:** `winget install ffmpeg` is recommended (sources from gyan.dev, auto-configures PATH). If winget is slow, download directly from gyan.dev.

**After installation, verify again with the check commands above.**

### Why This Matters

- Missing `yt-dlp` → Download fails entirely
- Missing `ffmpeg` → Transcoding fails, videos stay in incompatible codecs (AV1/VP9) that won't play in PowerPoint
- Missing `ffprobe` → Codec detection fails, script cannot decide whether to transcode

**Do NOT proceed until all three dependencies are verified.**

---

## Step 1: Acquire Video URLs

**⚠️ IMPORTANT: Do NOT use yt-dlp to search videos!**

- `yt-dlp` is for **downloading only**, not for searching
- Do NOT run commands like `yt-dlp "ytsearch:keyword"` or `yt-dlp "search:keyword"`
- Many users (especially in China) cannot access YouTube directly
- **ALWAYS use browser automation tools** to search for videos on accessible platforms

### Method A: User-provided

The user directly provides the video URL(s). Skip to Step 2.

### Method B: Browser Automation

Use browser automation to search for and extract video URLs:

**⚠️ For users in China: STRONGLY RECOMMEND Bilibili!**

Bilibili (bilibili.com) is China's largest video platform with:
- Best download speed and stability
- No VPN required
- Rich content library
- yt-dlp native support

**Recommended Search Platforms:**

| Platform | URL Pattern | Priority |
|----------|-------------|----------|
| **Bilibili** | `https://search.bilibili.com/all?keyword=keyword` | ⭐⭐⭐ **BEST for China** |
| Bing Video | `https://www.bing.com/videos/search?q=keyword+site:bilibili.com` | ⭐⭐ Backup option |
| 抖音/TikTok CN | `https://www.douyin.com/search/keyword` | ⭐ Alternative |
| 微博视频 | `https://s.weibo.com/weibo?q=keyword` | ⭐ Alternative |

**Workflow:**
1. Start browser in headless mode
2. Open Bilibili search page (recommended) or other platform
3. Snapshot the page to find video links
4. Extract video URLs from the page
5. Close browser

---

## Step 2: Download and Transcode

Call the script with obtained URLs:

```bash
python scripts/video_downloader.py "keyword" \
  --urls "URL1" "URL2" "URL3"
```

### Parameters

| Parameter        | Description                    | Default Value      |
| ---------------- | ------------------------------ | ------------------ |
| `keyword`        | Keyword (used for folder name) | Required           |
| `--urls`         | List of video URLs             | -                  |
| `--count`        | Number of videos to download   | 3                  |
| `--max-duration` | Maximum duration (minutes)     | -                  |
| `--quality`      | Quality (4k/1080p/720p/480p)   | 720p               |
| `--output-dir`   | Output directory               | ~/Downloads/videos |

### Transcoding Policy

| Codec              | Handling                        | Reason                                    |
| ------------------ | ------------------------------- | ----------------------------------------- |
| H.264/H.265/MPEG-4 | ✅ Direct copy (PPT-compatible) | PowerPoint natively supports these codecs |
| AV1/VP9            | ❌ Transcode to H.264           | PowerPoint cannot play these codecs       |

**Why H.264?** H.264 is the most widely supported video codec. Nearly all presentation software (PowerPoint, Keynote, Google Slides) can play H.264 videos without issues.

---

## Step 3: Use Output Files

### Output Structure

```
{output_dir}/
└── {keyword}_YYYYMMDD_HHMMSS/
    ├── 01_video.mp4                    ← Original downloaded file
    ├── 02_video.mp4
    ├── download_report.md              ← Download summary report
    └── ppt_compatible/                 ← Use files here for PPT
        ├── 01_video.mp4
        └── 02_video.mp4
```

**For PowerPoint insertion, always use files from `ppt_compatible/` folder.**

### Report Content

The `download_report.md` contains:
- Total videos requested vs successfully downloaded
- Transcoded count (AV1/VP9 → H.264)
- Already compatible count (direct copy)
- Output directory structure

---

## Complete Example

**User**: "Download 3 videos of GuAiling from Bilibili"

**Workflow**:

```bash
# Step 0: Check dependencies
yt-dlp --version
ffmpeg -version
ffprobe -version

# Step 1: Get URLs using browser automation (NOT yt-dlp search!)
# Option 1: Bing Video with site filter
browser_use(action="start", headed=False)
browser_use(action="open", url="https://www.bing.com/videos/search?q=GuAiling+site:bilibili.com")
browser_use(action="snapshot")
# Extract video URLs from the page...

# Option 2: Or search directly on Bilibili
# browser_use(action="open", url="https://search.bilibili.com/all?keyword=GuAiling")
# browser_use(action="snapshot")
# Extract video URLs from the page...

# Step 2: Download (with URLs obtained from Step 1)
python scripts/video_downloader.py "GuAiling" \
  --urls "URL1" "URL2" "URL3"

# Step 3: Use output
# Files ready in ~/Downloads/videos/GuAiling_.../ppt_compatible/
```

**Output:**

```
✅ Done!
📁 ~/Downloads/videos/GuAiling_20260401_151820/
📄 download_report.md
💡 Use files in ppt_compatible/ for PPT insertion
```

---

## For Sites Requiring Login

This skill does NOT support authenticated downloads. Use yt-dlp directly:

```bash
# Load cookies from browser
yt-dlp --cookies-from-browser chrome "VIDEO_URL"

# Or use cookie file
yt-dlp --cookies cookies.txt "VIDEO_URL"
```

---

**Author**: pax