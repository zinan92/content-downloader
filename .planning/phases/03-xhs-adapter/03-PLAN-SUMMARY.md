---
phase: "03"
plan: "PLAN"
subsystem: xhs-adapter
tags: [xhs, xiaohongshu, http-api, sidecar, adapter]
dependency_graph:
  requires: [01-scaffold-core, 02-douyin-adapter]
  provides: [xhs-download-single, xhs-download-profile-stub, xhs-sidecar-check]
  affects: [content_downloader.router, content_downloader.cli]
tech_stack:
  added: []
  patterns: [adapter-protocol, sidecar-http-client, async-context-manager, pydantic-models]
key_files:
  created:
    - content_downloader/adapters/xhs/__init__.py
    - content_downloader/adapters/xhs/api_client.py
    - content_downloader/adapters/xhs/mapper.py
    - content_downloader/adapters/xhs/adapter.py
    - content_downloader/adapters/xhs/sidecar.py
    - tests/adapters/xhs/test_api_client.py
    - tests/adapters/xhs/test_mapper.py
    - tests/adapters/xhs/test_adapter.py
    - tests/adapters/xhs/test_sidecar.py
    - tests/adapters/xhs/fixtures/note_gallery.json
    - tests/adapters/xhs/fixtures/note_video.json
  modified:
    - content_downloader/router.py
    - content_downloader/cli.py
decisions:
  - "XHSDownloadError(RuntimeError) wraps DownloadError Pydantic model — DownloadError is not BaseException so cannot be raised directly; wrapper preserves structured error payload via .download_error attribute"
  - "download_profile returns DownloadResult(unsupported) not raise — consistent with batch API design; caller gets structured result, not exception"
metrics:
  duration: "~15 min"
  completed: "2026-03-29"
  tasks: 7
  files: 13
---

# Phase 03 Plan PLAN: XHS Adapter Summary

**One-liner:** XHS (小红书) adapter via XHS-Downloader HTTP sidecar — async client, note mapper, image/video download, sidecar health check.

## What Was Built

A complete XHS platform adapter that communicates with a locally running XHS-Downloader instance via its HTTP API. Pure HTTP client — no XHS-Downloader source code embedded.

### Components

| File | Purpose |
|------|---------|
| `api_client.py` | `XHSAPIClient` — async httpx client for `POST /xhs/detail` and health check |
| `mapper.py` | `note_to_content_item()` — maps raw XHS API response to `ContentItem` |
| `adapter.py` | `XHSAdapter` — orchestrates download_single (gallery + video) and download_profile |
| `sidecar.py` | `XHSSidecar` — health check wrapper with human-readable startup instructions |

### URL Patterns Handled

- `xiaohongshu.com/explore/{note_id}` → single note
- `xiaohongshu.com/discovery/item/{note_id}` → single note
- `xhslink.com/{short_code}` → single note (short link)
- `xiaohongshu.com/user/profile/{user_id}` → profile (returns unsupported + workaround)

## Test Results

- **47 tests**, all passing
- Coverage: `api_client.py` 100%, `mapper.py` 100%, `sidecar.py` 100%, `adapter.py` 88%
- All HTTP calls mocked — no real network access required

## Verification Checklist

- [x] `pip install -e .` succeeds
- [x] `python -m content_downloader platforms` shows xhs [ready]
- [x] `XHSAdapter.can_handle()` matches all XHS URL formats
- [x] Mock test: download_single gallery note → img_01.jpg... + content_item.json
- [x] Mock test: download_single video note → video.mp4 + content_item.json
- [x] Mock test: XHS-Downloader not available → XHSDownloadError(service_unavailable)
- [x] Mock test: API returns empty → XHSDownloadError(not_found)
- [x] Mock test: download_profile → DownloadResult(unsupported) + workaround
- [x] ContentItem fields complete: likes/comments/shares/collects populated
- [x] All tests pass, coverage >85%

## Commits

| Hash | Task | Description |
|------|------|-------------|
| af27d92 | Task 1 | XHS-Downloader HTTP API client |
| 0a7c340 | Task 2 | XHS note detail to ContentItem mapper |
| a181173 | Task 3 | XHS adapter download_single |
| 5feae02 | Tasks 4+5 | download_profile unsupported + XHSSidecar |
| aac4bc9 | Task 6 | Register XHSAdapter in router, mark platform ready |
| 586002d | Task 7 | Unit tests — 47 tests, all mock HTTP |
| a1f0074 | Auto-fix | XHSDownloadError exception class |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] DownloadError is not raisable — added XHSDownloadError exception**

- **Found during:** Task 7 (tests)
- **Issue:** The plan spec said "raise DownloadError(...)" but `DownloadError` is a Pydantic BaseModel, not a BaseException subclass. Python raises `TypeError` when attempting to raise a non-exception.
- **Fix:** Added `XHSDownloadError(RuntimeError)` in `adapter.py` that wraps `DownloadError` with a `.download_error` attribute for structured access. Tests updated to use `pytest.raises(XHSDownloadError)` and `exc.download_error.error_type`.
- **Files modified:** `content_downloader/adapters/xhs/adapter.py`, `content_downloader/adapters/xhs/__init__.py`, `tests/adapters/xhs/test_adapter.py`
- **Commit:** a1f0074

## Known Stubs

- `download_profile` returns `DownloadResult(errors=[DownloadError(unsupported)])` — this is intentional per plan (Task 4 spec explicitly states this as the implementation strategy). A future plan can add real profile batch download once XHS-Downloader exposes a creator API endpoint.

## Self-Check: PASSED

Files exist:
- content_downloader/adapters/xhs/api_client.py: FOUND
- content_downloader/adapters/xhs/mapper.py: FOUND
- content_downloader/adapters/xhs/adapter.py: FOUND
- content_downloader/adapters/xhs/sidecar.py: FOUND
- tests/adapters/xhs/test_adapter.py: FOUND

Commits exist: af27d92, 0a7c340, a181173, 5feae02, aac4bc9, 586002d, a1f0074 — all in git log.
