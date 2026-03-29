---
phase: "02-douyin-adapter"
plan: "PLAN"
subsystem: "douyin-adapter"
tags: ["adapter", "douyin", "signing", "migration", "httpx"]
dependency_graph:
  requires: ["01-scaffold-core"]
  provides: ["douyin-adapter", "xbogus-signing", "abogus-signing"]
  affects: ["router", "cli"]
tech_stack:
  added: ["gmssl>=3.2.2"]
  patterns: ["adapter-protocol", "xbogus-rc4-md5-signing", "abogus-sm3-sm4-signing", "httpx-async-client"]
key_files:
  created:
    - content_downloader/adapters/douyin/__init__.py
    - content_downloader/adapters/douyin/xbogus.py
    - content_downloader/adapters/douyin/abogus.py
    - content_downloader/adapters/douyin/ms_token.py
    - content_downloader/adapters/douyin/cookie_manager.py
    - content_downloader/adapters/douyin/api_client.py
    - content_downloader/adapters/douyin/mapper.py
    - content_downloader/adapters/douyin/adapter.py
    - tests/adapters/douyin/test_mapper.py
    - tests/adapters/douyin/test_api_client.py
    - tests/adapters/douyin/test_adapter.py
    - tests/adapters/douyin/test_short_link.py
    - tests/adapters/douyin/fixtures/aweme_detail.json
    - tests/adapters/douyin/fixtures/user_post_page1.json
    - tests/adapters/douyin/fixtures/user_post_page2.json
  modified:
    - pyproject.toml
    - content_downloader/router.py
    - content_downloader/cli.py
    - tests/test_router.py
    - tests/test_cli.py
decisions:
  - "httpx replaces aiohttp for HTTP calls — consistent with project deps, simpler async context"
  - "XBogus/ABogus algorithms copied exactly from source — no simplification, preserves signing correctness"
  - "CookieManager simplified to JSON-file/dict only — no Playwright, lowers dependency surface"
  - "ABogus treated as optional import — falls back to XBogus gracefully if gmssl unavailable"
  - "Tasks 4 (download_profile) and 5 (short link) implemented together in adapter.py with Task 3"
metrics:
  duration: "~11 min"
  completed_date: "2026-03-29"
  tasks_completed: 8
  tests_added: 45
  files_created: 15
  files_modified: 5
  coverage_douyin_adapter: "87-97%"
  coverage_overall: "83%"
---

# Phase 2 Plan 1: Douyin Adapter Summary

**One-liner:** Migrated douyin-downloader-1 core to adapter pattern — XBogus/ABogus signing, httpx API client, no-watermark URL extraction, profile pagination with stagnation guard.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 8 | Dependencies update | 6a0776d | pyproject.toml |
| 1 | Signing & auth utilities | 775ad02 | xbogus.py, abogus.py, ms_token.py, cookie_manager.py |
| 2 | API client | bbb44e4 | api_client.py |
| 3+4+5 | Adapter + mapper + short link | e5b83e1 | adapter.py, mapper.py |
| 6 | Router registration + CLI | a12319b | router.py, cli.py |
| 7 | Unit tests | ca2f5aa | 4 test files + 3 fixtures |

## What Was Built

### Signing Utilities (Task 1)
- **xbogus.py** — Exact copy of XBogus signing algorithm (MD5+RC4+custom base64). Signs douyin.com URLs with `X-Bogus=` parameter.
- **abogus.py** — Exact copy of ABogus signing algorithm (SM3 hash via gmssl + custom transform). Preferred over XBogus when available.
- **ms_token.py** — Fetches real msToken from mssdk endpoint (via F2 config), falls back to random 184-char token. No yaml dependency change needed (pyyaml already in deps).
- **cookie_manager.py** — Simplified to JSON file + dict loading only. Removed Playwright browser cookie capture.

### API Client (Task 2)
- **api_client.py** — Async Douyin web API client. Ports `get_video_detail`, `get_user_post`, `resolve_short_url`, signing methods. Replaced aiohttp with httpx. Retry logic (3 attempts with exponential backoff) preserved. Removed browser fallback and non-post user modes (out of Phase 2 scope).

### Adapter (Tasks 3+4+5)
- **mapper.py** — Converts raw aweme_data dict to ContentItem. Handles video and gallery content types. Maps all stats fields (likes/comments/shares/collects/views).
- **adapter.py** — Full DouyinAdapter implementing PlatformAdapter protocol:
  - `can_handle()` — matches douyin.com/video/*, douyin.com/user/*, v.douyin.com/*
  - `download_single()` — resolves short links → extracts aweme_id → fetches API → extracts no-watermark URL → downloads video+cover → writes metadata.json+content_item.json
  - `download_profile()` — paginates user posts with limit/since filters and stagnation guard
  - No-watermark URL extraction migrated from `downloader_base.py` lines 482-527

### Router & CLI (Task 6)
- `router.get_adapter()` now returns `DouyinAdapter` for douyin URLs
- `router.get_adapter()` accepts optional `cookies_path` parameter
- CLI `download` command gets `--cookies path/to/cookies.json` option
- `platforms` command shows douyin as `[ready]`

### Tests (Task 7)
- **test_mapper.py** — 9 tests covering field mapping, stat defaults, gallery detection, title truncation
- **test_api_client.py** — 16 tests covering video detail, user post pagination, URL normalization, signing, short URL resolution
- **test_adapter.py** — 14 tests covering download_single directory structure, profile pagination, limit, since filter, stagnation guard, error recording
- **test_short_link.py** — 7 tests covering short URL resolution flow end-to-end

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `__init__.py` circular import at module load time**
- **Found during:** Task 1 verification
- **Issue:** `__init__.py` tried to import `DouyinAdapter` before `adapter.py` existed, causing import failure for all signing utilities
- **Fix:** Changed `__init__.py` to a lazy comment; direct imports used in router
- **Files modified:** `__init__.py`
- **Commit:** 775ad02 (same commit)

**2. [Rule 1 - Bug] Pre-existing tests expected DouyinAdapter to be StubAdapter**
- **Found during:** Task 7 full test run
- **Issue:** `test_router.py::test_douyin_returns_stub_adapter` and `test_cli.py::test_stub_adapter_exits_gracefully` failed because douyin is now a real adapter
- **Fix:** Updated test_router.py to assert DouyinAdapter; updated test_cli.py to use XHS URL (still stub)
- **Files modified:** `tests/test_router.py`, `tests/test_cli.py`
- **Commit:** ca2f5aa

## Verification Checklist

- [x] `pip install -e .` succeeds (gmssl dependency)
- [x] `python -m content_downloader platforms` lists douyin as [ready]
- [x] `DouyinAdapter.can_handle()` matches all douyin URL formats
- [x] Mock test: `download_single` produces correct directory structure
- [x] Mock test: `download_profile` with limit=3 produces 3 items
- [x] Mock test: short link resolution calls `resolve_short_url` before fetch
- [x] Mock test: no-watermark URL selection prefers `watermark=0` candidates
- [x] ContentItem fields complete: likes/comments/shares/collects/views populated
- [x] All 161 tests pass, 83% overall coverage

## Known Stubs

None — all adapter methods are fully implemented.

## Self-Check: PASSED

All committed files verified to exist:
- `/Users/wendy/work/content-co/content-downloader/content_downloader/adapters/douyin/adapter.py` — FOUND
- `/Users/wendy/work/content-co/content-downloader/content_downloader/adapters/douyin/api_client.py` — FOUND
- `/Users/wendy/work/content-co/content-downloader/content_downloader/adapters/douyin/xbogus.py` — FOUND
- `/Users/wendy/work/content-co/content-downloader/content_downloader/adapters/douyin/abogus.py` — FOUND

Commits verified in git log:
- `6a0776d` chore(02-PLAN): add gmssl dependency
- `775ad02` feat(02-PLAN): add douyin signing and auth utilities
- `bbb44e4` feat(02-PLAN): add Douyin API client
- `e5b83e1` feat(02-PLAN): add DouyinAdapter download_single
- `a12319b` feat(02-PLAN): register DouyinAdapter in router
- `ca2f5aa` test(02-PLAN): add Douyin adapter unit tests
