---
name: audio-downloader
version: 0.0.1
description: 批量下载网站音频资源，支持需要登录的网站，自动去重和生成报告
triggers:
  - 下载音频
  - 爬取音频
  - 批量下载 mp3、wav、m4a 等音频格式
  - 保存网站音频
  - download audio
  - scrape audio files
---

# Audio Downloader

批量下载网站音频资源，支持需要登录的网站，自动去重和生成报告。

## 📖 核心流程

### 1. 访问页面

```python
browser_use(action="open", url=target_url)
browser_use(action="snapshot")  # 检查是否需要登录
```

### 2. 判断意图

- 用户说"下载全部"、"批量下载" → 下载播放列表所有音频
- 用户说"下载这个"、"保存音频" → 仅下载当前音频

### 3. 收集音频 URL 并保存

#### 当前音频

```javascript
() => {
  const audio = document.querySelector('audio');
  if (!audio) return JSON.stringify({urls: []});
  const url = audio.src || audio.querySelector('source')?.src;
  return JSON.stringify({urls: [{index: 1, url, name: document.title || 'audio'}]});
}
```

#### 播放列表

根据页面特点选择方法：

1. **网络拦截**：拦截 fetch/XHR 获取音频 URL
2. **源码提取**：从页面源码或全局变量匹配音频 URL  
3. **点击加载**：逐个点击播放列表项，从 `<audio>` 标签获取 URL

#### 保存 URL 列表

将收集的 URL 保存为 JSON 文件：

```json
{
  "urls": [
    {"index": 1, "name": "音频名称", "url": "https://..."},
    {"index": 2, "name": "音频名称", "url": "https://..."}
  ]
}
```

### 4. 获取认证信息

```javascript
() => JSON.stringify({
  cookies: document.cookie,
  referer: window.location.href
})
```

### 5. 批量下载

```bash
python scripts/audio_downloader.py urls.json -k "关键词" -r "Referer" -c "Cookie"
```

## 📊 命令行参数

```
python scripts/audio_downloader.py url_file -k KEYWORD -r REFERER [-c COOKIES] [-d DELAY]

参数:
  url_file    URL JSON 文件
  -k          关键词（必需）
  -r          Referer URL（必需）
  -c          Cookie 字符串
  -d          下载间隔秒数
```

---

**Version**: 0.0.1
**Author**: pax
