# References

Platform-specific documentation for content-downloader adapters.

## Structure

```
references/
└── (platform docs to be added as needed)
```

## Platform-Specific Notes

### Douyin
- Requires cookies for authentication (see `cookies.json.example` at repo root)
- XBogus signing with gmssl; Playwright fallback if signing fails
- Profile batch download supports `--limit` and `--since` for incremental downloads

### Xiaohongshu
- Auto-managed XHS-Downloader sidecar — no manual auth needed
- Supports single posts and image galleries

### WeChat OA
- Zero-config HTML parsing
- Inline images are downloaded alongside article text

### X/Twitter
- Uses yt-dlp subprocess wrapper
- Supports videos, images, and text-only tweets
