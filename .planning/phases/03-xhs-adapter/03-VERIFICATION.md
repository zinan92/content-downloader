---
phase: 03-xhs-adapter
verified: 2026-03-29T10:52:25Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 03: XHS Adapter Verification Report

**Phase Goal:** XHS-Downloader HTTP API 集成，小红书笔记下载可用
**Verified:** 2026-03-29T10:52:25Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                 | Status     | Evidence                                                                 |
|----|-----------------------------------------------------------------------|------------|--------------------------------------------------------------------------|
| 1  | Single XHS note URL triggers download of images/video + metadata      | VERIFIED   | `adapter.py` `download_single()` writes `media/`, `metadata.json`, `content_item.json`; mock test confirms output |
| 2  | Profile URL returns unsupported error with workaround instructions    | VERIFIED   | `download_profile()` returns `DownloadResult(errors=[DownloadError(unsupported)])`; test confirms error message contains "creator" |
| 3  | XHS-Downloader sidecar unavailable raises informative error           | VERIFIED   | `is_available()` check before detail call; `XHSDownloadError(service_unavailable)` raised with `python main.py api` instructions |
| 4  | Output ContentItem format consistent with other adapters (platform, content_id, media_files, engagement fields) | VERIFIED | `mapper.py` populates all 15 ContentItem fields; `likes/comments/shares/collects/views` tested in `test_mapper.py` |
| 5  | All XHS adapter unit tests pass with >85% coverage                   | VERIFIED   | 47/47 tests pass; `api_client.py` 100%, `mapper.py` 100%, `sidecar.py` 100%, `adapter.py` 88% |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact                                           | Expected                                      | Status    | Details                                                          |
|----------------------------------------------------|-----------------------------------------------|-----------|------------------------------------------------------------------|
| `content_downloader/adapters/xhs/__init__.py`      | Package entry; exports XHSAdapter             | VERIFIED  | Exports `XHSAdapter`, `XHSDownloadError`                         |
| `content_downloader/adapters/xhs/api_client.py`    | Async httpx client for POST /xhs/detail       | VERIFIED  | 103 lines; `get_note_detail()`, `is_available()`, context manager |
| `content_downloader/adapters/xhs/mapper.py`        | Raw API dict → ContentItem                    | VERIFIED  | 99 lines; maps all 15 ContentItem fields including engagement     |
| `content_downloader/adapters/xhs/adapter.py`       | `download_single` + `download_profile`        | VERIFIED  | 317 lines; both methods implemented, error handling present       |
| `content_downloader/adapters/xhs/sidecar.py`       | Health check + startup instructions           | VERIFIED  | 43 lines; `check_health()` + `get_start_instructions()`          |
| `tests/adapters/xhs/test_api_client.py`            | Mock HTTP tests for API client                | VERIFIED  | 10 test cases; covers gallery, video, empty, error, timeout      |
| `tests/adapters/xhs/test_mapper.py`                | Note → ContentItem mapping tests              | VERIFIED  | 17 test cases; gallery + video + edge cases                      |
| `tests/adapters/xhs/test_adapter.py`               | download_single + download_profile tests      | VERIFIED  | 14 test cases; all error paths covered                           |
| `tests/adapters/xhs/test_sidecar.py`               | Sidecar health check tests                   | VERIFIED  | 5 test cases; health up/down + instructions                      |
| `tests/adapters/xhs/fixtures/note_gallery.json`    | Gallery note fixture                          | VERIFIED  | Present in `tests/adapters/xhs/fixtures/`                        |
| `tests/adapters/xhs/fixtures/note_video.json`      | Video note fixture                            | VERIFIED  | Present in `tests/adapters/xhs/fixtures/`                        |

---

### Key Link Verification

| From                  | To                        | Via                            | Status  | Details                                                                          |
|-----------------------|---------------------------|--------------------------------|---------|----------------------------------------------------------------------------------|
| `router.py`           | `XHSAdapter`              | `if platform == "xhs":` branch | WIRED   | Lines 118-120 in `router.py`; lazy import and instantiation confirmed             |
| `adapter.py`          | `XHSAPIClient`            | `async with XHSAPIClient()`    | WIRED   | Used in both `download_single()` and `_save_note()`; health check + detail call  |
| `adapter.py`          | `note_to_content_item`    | direct call in `_save_note()`  | WIRED   | Line 247; result flows to `content_item.json` write                              |
| `adapter.py`          | `XHSSidecar` instructions | inline constant `_SERVICE_UNAVAILABLE_MESSAGE` | WIRED | Same message used in adapter and sidecar; consistent content                    |
| `cli.py`              | `xhs` platform            | `list_supported_platforms()`   | WIRED   | `xhs` listed as `[ready]` in `platforms` command (line 293)                      |
| `router.py`           | XHS URL patterns          | `_URL_PATTERNS` list entries   | WIRED   | 4 XHS patterns registered (explore, discovery, xhslink, user/profile)            |

---

### Requirements Coverage

| Requirement | Description                                              | Status    | Evidence                                                              |
|-------------|----------------------------------------------------------|-----------|-----------------------------------------------------------------------|
| ADAPT-04    | 小红书 adapter — 单条笔记 URL 下载（图片/视频 + metadata） | SATISFIED | `download_single()` handles gallery and video; writes media/ + JSON files |
| ADAPT-05    | 小红书 adapter — profile URL 批量下载                    | SATISFIED | `download_profile()` implemented; returns structured unsupported error with workaround (plan explicitly specifies this as the implementation strategy for now) |
| ADAPT-06    | 小红书 adapter — 通过 XHS-Downloader HTTP API（sidecar）  | SATISFIED | `XHSAPIClient` calls `POST /xhs/detail`; `XHSSidecar.check_health()` wraps `GET /`; no XHS-Downloader source embedded |

Note: ADAPT-05 is marked SATISFIED because the plan explicitly documents `download_profile` returning an unsupported result as the intentional implementation (Task 4 spec). This is a known stub with a clear workaround, not a missing feature.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `adapter.py` | 157 | `user_id = ""` (initial value, overwritten by regex match) | Info | Not a stub — correctly overwritten by `_PROFILE_URL_RE.search()` on line 159 |
| `adapter.py` | 162 | `DownloadError(... error_type="unsupported")` | Info | Intentional per plan spec (Task 4); workaround instructions are substantive |

No blockers or warnings. The `views=0` in `mapper.py` line 96 is documented behavior ("XHS does not expose view counts"), not a stub.

---

### Human Verification Required

#### 1. Real sidecar integration smoke test

**Test:** Start a real XHS-Downloader instance (`python main.py api` at port 5556), then run `python -m content_downloader download "https://www.xiaohongshu.com/explore/<real_note_id>"`.
**Expected:** Files appear in `output/xhs/<author_id>/<note_id>/` — media files, `metadata.json`, `content_item.json`. `manifest.jsonl` gets one new line.
**Why human:** Requires a real XHS-Downloader instance, a valid cookie, and a live note URL. Cannot verify mock-only behavior against real API shape.

#### 2. `python -m content_downloader platforms` output

**Test:** Run the command in a working virtualenv.
**Expected:** Output shows `xhs [ready]` alongside `douyin [ready]`.
**Why human:** CLI entry point untested by the unit test suite; `cli.py` has 0% coverage in the run above.

---

### Gaps Summary

No gaps found. All 5 observable truths are verified. All 11 artifacts exist and are substantive. All 6 key links are wired. Requirements ADAPT-04, ADAPT-05, ADAPT-06 are satisfied. 47 tests pass with module-level coverage meeting the >85% target for all XHS-specific files.

The only open item is the intentional `download_profile` unsupported stub, which is documented as the correct v1 behavior in the plan and carries explicit workaround instructions for users.

---

### Commit Verification

All 7 commits claimed in SUMMARY frontmatter were found in git log:

| Hash    | Task | Description                                         |
|---------|------|-----------------------------------------------------|
| af27d92 | 1    | feat(03-xhs): XHS-Downloader HTTP API client        |
| 0a7c340 | 2    | feat(03-xhs): XHS note detail to ContentItem mapper |
| a181173 | 3    | feat(03-xhs): XHS adapter download_single           |
| 5feae02 | 4+5  | feat(03-xhs): download_profile unsupported + sidecar|
| aac4bc9 | 6    | feat(03-xhs): register XHSAdapter in router         |
| 586002d | 7    | test(03-xhs): 47 tests, all mock HTTP               |
| a1f0074 | fix  | fix(03-xhs): add XHSDownloadError exception class   |

---

_Verified: 2026-03-29T10:52:25Z_
_Verifier: Claude (gsd-verifier)_
