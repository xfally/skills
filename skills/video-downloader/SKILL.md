---
name: video-downloader
description: >
  Use this skill when the user wants to download videos.
  Two ways to get video URLs:
  1) The agent uses browser automation tools (headless mode recommended) to extract URLs.
  2) The user provides URLs directly.
  Then download and convert to PPT-compatible formats.
metadata: { "copaw": { "emoji": "🎬", "requires": {} } }
---

# Video Downloader Skill

## Features

Download videos and intelligently transcode them into PPT-compatible formats.

## URL Acquisition Methods

### Method 1: Browser Automation Tools (Recommended)

Use browser automation tools (headless mode recommended) to search for and extract video URLs:

**Example (Copaw uses the tool browser_use, which is based on Playwright, to extract URLs):**

```json
{"action": "start", "headed": false}
{"action": "open", "url": "https://cn.bing.com/videos/search?q=GuAiling+site:bilibili.com"}
{"action": "snapshot"}
{"action": "eval", "code": "Extract Bilibili URL"}
{"action": "close"}
```

### Method 2: User-provided

The user directly provides the video URL(s).

## Download and Transcoding

After obtaining the URL(s), call the script to download:

```bash
python scripts/video_downloader.py "keyword" \
  --urls "URL1" "URL2" "URL3"
```

## Output Structure

```
{output_dir}/
└── {keyword}_YYYYMMDD_HHMMSS/
    ├── 01_video.mp4
    └── ppt_compatible/      ← Use files in this folder for PPT insertion
        └── 01_video.mp4
```

## Transcoding Policy

| Codec              | Handling                        |
| ------------------ | ------------------------------- |
| H.264/H.265/MPEG-4 | ✅ Direct copy (PPT-compatible) |
| AV1/VP9            | ❌ Transcode to H.264           |

## Parameters

| Parameter        | Description                    | Default Value      |
| ---------------- | ------------------------------ | ------------------ |
| `keyword`        | Keyword (used for folder name) | Required           |
| `--urls`         | List of video URLs             | -                  |
| `--count`        | Number of videos to download   | 3                  |
| `--max-duration` | Maximum duration (minutes)     | -                  |
| `--quality`      | Quality (4k/1080p/720p/480p)   | 720p               |
| `--output-dir`   | Output directory               | ~/Downloads/videos |

## Example

**User**: "Download 3 videos of GuAiling"

**Assistant**:

1. **Get URLs** (choose one):

   - Method 1: Use browser automation tools (headless mode recommended) to search and extract
   - Method 2: Ask the user to provide them

2. **Download**:

   ```bash
   python scripts/video_downloader.py "GuAiling" \
     --urls "URL1" "URL2" "URL3"
   ```

3. **Completed**:

   ```
   ✅ Done!
   📁 ~/Downloads/videos/Gu_Ailing_20260304_151820/
   💡 Use files in the ppt_compatible folder for PPT insertion
   ```

## Dependencies

- `yt-dlp` - Downloading
- `ffmpeg` - Transcoding
- `ffprobe` - Codec detection
- Browser automation tools (optional) - Automated search

---

**Version**: 0.0.1
**Author**: pax

---
