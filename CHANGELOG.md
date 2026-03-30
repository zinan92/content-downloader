# Changelog

## [0.1.0] - 2026-03-30

### Added
- Unified content downloader with adapter pattern for 4 platforms
- **Douyin**: video + gallery download, no-watermark, profile batch (--limit/--since), short link resolve
- **Xiaohongshu**: video + image gallery via XHS-Downloader sidecar (auto-install + auto-start)
- **WeChat Official Account**: article HTML + inline images + audio ID extraction
- **X/Twitter**: video + image + text-only tweets via yt-dlp
- Standardized `ContentItem` data model (Pydantic v2, frozen/immutable)
- `manifest.jsonl` append-only index with file-lock concurrency safety
- Deduplication: already-downloaded content_id auto-skipped
- `text.txt` standalone readable text file per item
- CLI: `download`, `list`, `platforms` commands
- 303 tests, 85% coverage
