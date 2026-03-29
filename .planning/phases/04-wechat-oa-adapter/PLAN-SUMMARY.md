---
phase: "04-wechat-oa-adapter"
plan: "PLAN"
subsystem: "wechat-oa-adapter"
tags: ["adapter", "wechat", "html-parser", "scraping"]
dependency_graph:
  requires: ["01-scaffold-core"]
  provides: ["wechat_oa adapter — download public WeChat OA articles"]
  affects: ["router.py", "content_downloader/adapters/wechat_oa/"]
tech_stack:
  added: ["html.parser (stdlib)", "re (stdlib)"]
  patterns: ["PlatformAdapter protocol", "async httpx download", "immutable ContentItem"]
key_files:
  created:
    - content_downloader/adapters/wechat_oa/__init__.py
    - content_downloader/adapters/wechat_oa/parser.py
    - content_downloader/adapters/wechat_oa/adapter.py
    - tests/adapters/wechat_oa/__init__.py
    - tests/adapters/wechat_oa/test_parser.py
    - tests/adapters/wechat_oa/test_adapter.py
    - tests/adapters/wechat_oa/fixtures/sample_article.html
  modified:
    - content_downloader/router.py
decisions:
  - "stdlib html.parser + re instead of BeautifulSoup — WeChat HTML structure is fixed and consistent"
  - "audio voice_encode_fileid saved as text IDs, not downloaded — WeChat audio requires API auth"
  - "image download failures are non-fatal (logged + skipped) — aligns with SAFE-02"
  - "download_profile returns DownloadResult(unsupported) not raise — consistent with XHSAdapter pattern"
metrics:
  duration: "~7 minutes"
  completed_date: "2026-03-29"
  tasks: 3
  files: 8
---

# Phase 04 Plan PLAN: WeChat OA Adapter Summary

**One-liner:** WeChat Official Account article downloader — public HTML parsing via stdlib regex, extracts title/author/time/images/audio, 48 tests all passing, 100% coverage on new code.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | WeChatOA HTML Parser | 7777f1b | parser.py, __init__.py |
| 2 | WeChatOAAdapter | adeeeb1 | adapter.py |
| 3 | Register + Tests | 9820d4a | router.py, 4 test files |

## What Was Built

### Parser (`parser.py`)

`WeChatOAParser` fetches public mp.weixin.qq.com article pages via httpx and extracts:

- **Title**: `<h1 class="rich_media_title">` → falls back to `<meta property="og:title">`
- **Author**: `<a id="js_name">` → falls back to `<span class="rich_media_meta_text">`
- **Publish time**: `<em id="publish_time">` → falls back to `var ct = "unix_timestamp"` in JS
- **Body HTML**: `<div id="js_content">` contents
- **Images**: all `data-src="https://..."` attributes (WeChat lazy-loads images)
- **Audio**: `<mpvoice voice_encode_fileid="...">` attribute values

Also exposes `parse_html(html, url)` for direct HTML parsing without HTTP (used in tests).

### Adapter (`adapter.py`)

`WeChatOAAdapter` implements the full PlatformAdapter protocol:

- `can_handle(url)` — matches `mp.weixin.qq.com/s/*` (http and https)
- `download_single(url, output_dir)`:
  1. Fetches article HTML via parser
  2. Creates `output_dir/wechat_oa/{author}/{article_id}/media/`
  3. Saves body HTML to `media/article.html`
  4. Downloads images to `media/img_01.jpg`, `img_02.jpg`, ... (failures non-fatal)
  5. Saves audio voice_encode_fileid values to `media/audio_ids.txt` (if present)
  6. Writes `metadata.json` (title, author, publish_time, source_url, images, audio_urls)
  7. Writes `content_item.json` and returns `ContentItem`
- `download_profile(...)` — returns `DownloadResult(unsupported)` with workaround message

`_extract_article_id` handles both URL forms:
- Short: `mp.weixin.qq.com/s/{id}` → uses path segment
- Long: `mp.weixin.qq.com/s?__biz=...&mid=...&idx=...` → uses `mid_idx`

### Tests (48 tests)

- `test_parser.py`: 27 unit tests for every extraction function + `parse_html` + `fetch_article` (mocked httpx)
- `test_adapter.py`: 21 tests for `can_handle`, `_extract_article_id`, full `download_single` flow, `download_profile`, and router integration
- `fixtures/sample_article.html`: realistic WeChat OA article HTML with title, author, publish_time, images, mpvoice audio

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] datetime.utcnow() deprecated warning**
- **Found during:** Task 3 test run
- **Issue:** `datetime.utcnow()` produces DeprecationWarning in Python 3.12+
- **Fix:** Changed to `datetime.now(timezone.utc).isoformat()`
- **Files modified:** content_downloader/adapters/wechat_oa/adapter.py

None of the plan's core logic deviated. All three tasks executed exactly as specified.

## Verification

- `python -m content_downloader platforms` will show wechat_oa [via get_adapter routing]
- Mock tests: article HTML → title/author/time/images/audio correctly extracted ✓
- Mock tests: download_single → article.html + images + content_item.json ✓
- Mock tests: download_profile → unsupported DownloadResult ✓
- ContentItem content_type = "article" ✓
- 48/48 tests pass, wechat_oa adapter + parser at 100% coverage ✓

## Self-Check: PASSED

All files verified:
- `content_downloader/adapters/wechat_oa/__init__.py` — FOUND
- `content_downloader/adapters/wechat_oa/parser.py` — FOUND
- `content_downloader/adapters/wechat_oa/adapter.py` — FOUND
- `tests/adapters/wechat_oa/test_parser.py` — FOUND
- `tests/adapters/wechat_oa/test_adapter.py` — FOUND

All commits verified:
- 7777f1b (Task 1) — FOUND
- adeeeb1 (Task 2) — FOUND
- 9820d4a (Task 3) — FOUND
