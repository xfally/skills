---
name: audio-downloader
description: >
  Batch download audio files from websites, including sites requiring login.
  Trigger phrases: "download audio", "save audio", "批量下载音频", "下载音频", "爬取音频",
  "scrape audio", "mp3 download", "音频下载", "extract audio", "音频资源", "音频批量下载",
  "download mp3", "download m4a", "download wav", "audio playlist".
  Supports automatic deduplication and report generation.
---

# Audio Downloader Skill

Batch download audio files from websites with automatic deduplication and report generation.

---

## Step 0: Check Dependencies (CRITICAL)

**Before downloading any audio, you MUST verify curl is installed.**

### Check Command

```bash
curl --version
```

**Expected output:** prints curl version info (e.g., "curl 8.0.0")

### If Missing

| Platform    | Install Command                    |
| ----------- | ---------------------------------- |
| macOS/Linux | Usually pre-installed              |
| macOS       | `brew install curl`                |
| Linux       | `sudo apt install curl` (Debian)   |
| Windows     | `winget install curl`              |

---

## Step 1: Access Page and Check Login

**Always start with headless mode. Switch to headed mode only if login is required.**

### 1.1 Open in Headless Mode

```python
browser_use(action="start", headed=False)
browser_use(action="open", url=target_url)
browser_use(action="snapshot")
```

### 1.2 Check Login Requirement

Look for login indicators in the page:
- Login button/form
- "Please login" / "请登录" / "登录" text
- Captcha
- Restricted content placeholder
- Audio player not visible or disabled

### 1.3 Decision

| Login Required? | Action |
|----------------|--------|
| **No** | Continue with headless mode, proceed to Step 2 |
| **Yes** | Switch to headed mode for user login (see below) |

### 1.4 Switch to Headed Mode (If Login Required)

```python
browser_use(action="close")
browser_use(action="start", headed=True)
browser_use(action="open", url=target_url)
# Wait for user to complete login manually
# User should notify when login is complete
browser_use(action="snapshot")  # Verify login success
```

**Important:** After user completes login, verify the page shows logged-in state before proceeding.

---

## Step 2: Determine User Intent

- User says "download all", "批量下载" → Download entire playlist
- User says "download this", "保存音频" → Download current audio only

---

## Step 3: Collect Audio URLs

### Single Audio

```javascript
() => {
  const audio = document.querySelector('audio');
  if (!audio) return JSON.stringify({urls: []});
  const url = audio.src || audio.querySelector('source')?.src;
  return JSON.stringify({urls: [{index: 1, url, name: document.title || 'audio'}]});
}
```

### Playlist

Choose method based on page structure:

1. **Network interception**: Intercept fetch/XHR requests to get audio URLs
2. **Source extraction**: Extract audio URLs from page source or global variables
3. **Click-to-load**: Click each playlist item, extract URL from `<audio>` tag

### Save URL List

Save collected URLs as JSON:

```json
{
  "urls": [
    {"index": 1, "name": "Audio Title", "url": "https://..."},
    {"index": 2, "name": "Audio Title", "url": "https://..."}
  ]
}
```

---

## Step 4: Get Authentication Info

For sites requiring login, extract cookies and referer:

```javascript
() => JSON.stringify({
  cookies: document.cookie,
  referer: window.location.href
})
```

**Note:** This step is only needed if you used headed mode for login. For public pages without login, this step can be skipped.

---

## Step 5: Batch Download

```bash
python scripts/audio_downloader.py urls.json -k "keyword" -r "Referer" -c "Cookie"
```

### Parameters

| Parameter | Description | Required | Default |
| --------- | ----------- | -------- | ------- |
| `url_file` | URL JSON file path | Yes | - |
| `-k` | Keyword (for folder name) | Yes | - |
| `-r` | Referer URL | Yes | - |
| `-c` | Cookie string | No | - |
| `-d` | Download delay (seconds) | No | 0 |
| `-o` | Output directory | No | ~/Downloads/audios |

---

## Step 6: Use Output Files

### Output Structure

```
{output_dir}/
└── {keyword}_YYYYMMDD_HHMMSS/
    ├── 001_audio_name.mp3
    ├── 002_audio_name.m4a
    └── download_report.md
```

**Default output directory:** `~/Downloads/audios`

### Report Content

The `download_report.md` contains:
- Total audio items requested
- Unique audio files (after deduplication)
- Success/fail/skip counts
- Output directory structure

---

## Complete Example

**User**: "Download all audio from this playlist"

**Workflow**:

```bash
# Step 0: Check dependencies
curl --version

# Step 1: Access page and check login
browser_use(action="start", headed=False)
browser_use(action="open", url="https://example.com/playlist")
browser_use(action="snapshot")
# If login required: switch to headed=True, wait for user login

# Step 2: Determine intent (playlist vs single audio)

# Step 3: Collect audio URLs
# Extract URLs via JavaScript or network interception

# Step 4: Get auth info (if login was required)
# () => JSON.stringify({cookies: document.cookie, referer: window.location.href})

# Step 5: Download
python scripts/audio_downloader.py urls.json \
  -k "playlist_name" \
  -r "https://example.com/playlist" \
  -c "session_id=xxx"  # Only needed if login was required
  # -o "/custom/output/path"  # Optional: custom output directory

# Step 6: Check output
# Files in: ~/Downloads/audios/playlist_name_20260401_140000/
```

**Output:**

```
✅ Done! Success: 15, Fail: 0, Skip: 2
📁 ~/Downloads/audios/playlist_name_20260401_140000/
📄 download_report.md
```

---

**Author**: pax
