---
name: content-downloader
description: Unified content download from Douyin, Xiaohongshu, WeChat, and X/Twitter. Read this to know WHEN and HOW to use content-downloader.
---

# Content Downloader

Unified content download from multiple social platforms into standardized local files with metadata preservation.

## When to Use

Use `content-downloader` when the user has a **URL** and wants to **download content locally**.

| User says | Action |
|-----------|--------|
| "下载这个视频" / "grab this video" + URL | `content-downloader download <url>` |
| "下载这个博主所有视频" / "download all from this creator" | `content-downloader download <profile-url>` |
| "下载这篇公众号文章" | `content-downloader download <mp.weixin.qq.com-url>` |

## When NOT to Use

| User wants | Use instead |
|------------|-------------|
| Transcribe a local video | `content-extractor` or `videocut transcribe` |
| Rewrite content for another platform | `content-rewriter` |
| Edit a video | `videocut` |
| Analyze content trends | `content-intelligence` |

## Supported Platforms

| Platform | Single Content | Profile Batch | Auth Required |
|----------|---------------|---------------|---------------|
| Douyin (抖音) | Yes | Yes | Cookies required |
| Xiaohongshu (小红书) | Yes | Yes | Auto-managed sidecar |
| WeChat OA (公众号) | Yes | No | None |
| X/Twitter | Yes | No | None |

## Input

A platform content URL (HTTP/HTTPS):

```bash
# Douyin
content-downloader download https://douyin.com/video/xxx --cookies cookies.json

# Xiaohongshu
content-downloader download https://xiaohongshu.com/explore/xxx

# WeChat
content-downloader download https://mp.weixin.qq.com/s/xxx

# X/Twitter
content-downloader download https://x.com/user/status/xxx
```

## Output

Standardized directory structure per content item:

```
output/{platform}/{author_id}/{content_id}/
├── media/
│   ├── video.mp4          # or image files
│   └── cover.jpg
├── metadata.json           # Raw platform API response
├── content_item.json       # Standardized ContentItem (Pydantic model)
└── text.txt                # Plain text content
```

Plus a global `manifest.jsonl` for deduplication and indexing.

The `content_item.json` is the handoff contract consumed by `content-extractor`.

## CLI Reference

```bash
# Download single content
content-downloader download <url> [OPTIONS]

# Download creator profile
content-downloader download <profile-url> --limit 50 --since 2026-01-01

# List supported platforms
content-downloader platforms
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` / `-o` | `./output` | Root output directory |
| `--cookies` | None | Path to cookies.json (required for Douyin) |
| `--limit` / `-l` | 0 (all) | Max items for profile download |
| `--since` | None | ISO 8601 date for incremental profile download |
| `--force` / `-f` | False | Re-download existing items |

## Architecture

```
URL → Router (regex classification)
  → Platform Adapter (async download)
    → OutputManager (standardized directory structure)
      → ManifestManager (JSONL append-only index)
```

### Adapters

| Platform | Implementation | Notes |
|----------|---------------|-------|
| Douyin | XBogus signing + Playwright fallback | Cookie-based auth |
| Xiaohongshu | XHS-Downloader sidecar (auto-managed) | HTTP API integration |
| WeChat OA | HTML parsing | Zero-config |
| X/Twitter | yt-dlp subprocess wrapper | Media downloader |

## Dependencies

- Python 3.11+
- Platform-specific: yt-dlp (X/Twitter), Playwright (Douyin fallback)

## Configuration

| Path | Purpose | Required |
|------|---------|----------|
| `cookies.json` | Douyin authentication cookies | For Douyin only |

## Failure Modes

| Failure | Behavior |
|---------|----------|
| Unsupported URL | Error with supported platform list |
| Missing cookies (Douyin) | Error with cookie setup instructions |
| Network/API error | Retry with adapter-specific fallback chain |
| Already downloaded | Skip (unless `--force`) |

## Pipeline Position

```
content-downloader → content-extractor → content-rewriter → [publish]
```

This capability is the first stage. Its output directories are consumed by `content-extractor`.
