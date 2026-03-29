---
phase: 01-scaffold-core
plan: PLAN
subsystem: cli
tags: [python, click, pydantic, httpx, filelock, adapter-pattern, jsonl]

requires: []

provides:
  - ContentItem/DownloadError/DownloadResult Pydantic models
  - PlatformAdapter Protocol interface (runtime_checkable)
  - FixtureAdapter — deterministic test adapter with real file I/O
  - StubAdapter — placeholder for unimplemented platforms
  - URL router — classifies URLs to (platform, url_type)
  - OutputManager — writes standardized output directory structure
  - ManifestManager — file-locked JSONL append-only index with dedup
  - CLI — download / list / platforms commands via Click

affects:
  - 02-douyin-adapter
  - 03-xhs-adapter
  - 04-wechat-oa-adapter
  - 05-x-adapter

tech-stack:
  added:
    - click>=8.1 (CLI framework)
    - pydantic>=2.0 (frozen models, JSON validation)
    - httpx>=0.27 (HTTP client for real adapters in Phase 2+)
    - filelock>=3.13 (concurrent manifest writes)
    - pyyaml>=6.0 (config file support)
    - pytest + pytest-asyncio + pytest-cov (testing)
  patterns:
    - Adapter pattern — PlatformAdapter Protocol, each platform in its own module
    - Frozen Pydantic models — immutable ContentItem/DownloadResult
    - Append-only JSONL manifest with file lock for concurrency safety
    - Output directory convention: output/{platform}/{author_id}/{content_id}/

key-files:
  created:
    - pyproject.toml
    - content_downloader/models.py
    - content_downloader/adapters/base.py
    - content_downloader/adapters/fixture.py
    - content_downloader/adapters/stub.py
    - content_downloader/router.py
    - content_downloader/output.py
    - content_downloader/manifest.py
    - content_downloader/cli.py
    - tests/test_models.py
    - tests/test_fixture_adapter.py
    - tests/test_router.py
    - tests/test_output.py
    - tests/test_manifest.py
    - tests/test_cli.py
    - tests/test_integration.py

key-decisions:
  - "PlatformAdapter as Protocol (not ABC) — enables duck typing and easier testing without inheritance"
  - "Frozen Pydantic models for ContentItem — immutable by design, safe to pass across layers"
  - "StubAdapter for unimplemented platforms — router can list all 5 platforms; real adapters added in Phase 2+"
  - "filelock for manifest concurrency — process-safe for batch downloads and future parallel workers"
  - "Output directory written by adapter; OutputManager writes content_item.json — adapter owns media/metadata, manager owns the index"

patterns-established:
  - "Adapter pattern: each platform = one module in content_downloader/adapters/"
  - "URL router returns adapter instance via get_adapter(url) — callers never import adapters directly"
  - "Content directory path: output_dir/{platform}/{author_id}/{content_id}/"
  - "Manifest JSONL: one line per ContentItem, file-locked append, dedup by content_id"
  - "CLI --force bypasses dedup check; without force, second download of same URL is silently skipped"

requirements-completed:
  - CORE-01
  - CORE-02
  - CORE-03
  - CORE-04
  - CORE-05
  - CORE-06
  - CORE-07
  - TEST-01
  - TEST-04
  - SAFE-01
  - SAFE-02
  - SAFE-03
  - SAFE-04

duration: 8min
completed: 2026-03-29
---

# Phase 1: Scaffold + Core Summary

**Python CLI skeleton with adapter pattern, frozen Pydantic ContentItem model, file-locked JSONL manifest, and fixture adapter running full download flow — 116 tests, 93% coverage**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-29T09:32:58Z
- **Completed:** 2026-03-29T09:41:00Z
- **Tasks:** 9
- **Files modified:** 16 created

## Accomplishments

- Full Python package scaffold with `pyproject.toml`, entry point, `pip install -e .` working
- ContentItem / DownloadError / DownloadResult as frozen Pydantic v2 models with JSON round-trip validation
- PlatformAdapter Protocol interface with `can_handle`, `download_single`, `download_profile` — runtime_checkable
- FixtureAdapter: writes real files to disk (dummy MP4 + JPEG + metadata.json + content_item.json), deterministic, no network
- URL router with regex patterns for 5 platforms (douyin, xhs, wechat_oa, x, fixture) + UnsupportedPlatformError with helpful message
- OutputManager: creates `output/{platform}/{author_id}/{content_id}/media/` directory tree
- ManifestManager: thread-safe file-locked JSONL append with dedup via `contains(content_id)`
- CLI: `download` (single + profile, --limit, --since, --force), `list` (--platform filter), `platforms` commands
- 116 tests across 6 test files, 93% line coverage

## Task Commits

1. **Task 1: Project scaffold** — `07118f4` (feat)
2. **Task 2: Data models** — `df701ba` (feat)
3. **Task 3: Platform adapter interface** — `d56900e` (feat)
4. **Task 4: Fixture adapter** — `f4e59a3` (feat)
5. **Task 5: URL router** — `816d8d3` (feat)
6. **Task 6: Output manager** — `e9d8ef9` (feat)
7. **Task 7: Manifest manager** — `034b72a` (feat)
8. **Task 8: CLI entry point** — `1286f41` (feat)
9. **Task 9: Integration tests** — `2ce4cec` (feat)

## Files Created/Modified

- `pyproject.toml` — Python 3.11+ package config with click/httpx/pydantic/filelock deps
- `content_downloader/models.py` — ContentItem, DownloadError, DownloadResult (frozen Pydantic)
- `content_downloader/adapters/base.py` — PlatformAdapter Protocol
- `content_downloader/adapters/fixture.py` — Deterministic test adapter
- `content_downloader/adapters/stub.py` — Placeholder for unimplemented platforms
- `content_downloader/router.py` — URL classification and adapter routing
- `content_downloader/output.py` — Output directory structure writer
- `content_downloader/manifest.py` — File-locked JSONL manifest manager
- `content_downloader/cli.py` — Click CLI with download/list/platforms commands
- `tests/test_models.py` — 14 tests
- `tests/test_fixture_adapter.py` — 19 tests
- `tests/test_router.py` — 24 tests
- `tests/test_output.py` — 14 tests
- `tests/test_manifest.py` — 13 tests (including concurrent append test)
- `tests/test_cli.py` — 17 tests
- `tests/test_integration.py` — 15 end-to-end scenario tests

## Decisions Made

- Used PlatformAdapter as a `Protocol` rather than ABC — enables structural subtyping, no inheritance required for adapters
- Frozen Pydantic v2 models throughout — zero mutation risk, serialization built in
- StubAdapter registered for douyin/xhs/wechat_oa/x — router can list all platforms now, real implementations in Phase 2+
- `filelock` for concurrent manifest writes — process-safe, critical for future batch/parallel downloads
- Adapter owns writing media + metadata.json; OutputManager writes content_item.json — clear separation of responsibilities

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed setuptools build backend string**
- **Found during:** Task 1 (project scaffold)
- **Issue:** `setuptools.backends.legacy:build` is not a valid backend in setuptools 68+; pip install -e . failed
- **Fix:** Changed to `setuptools.build_meta` (correct backend name)
- **Files modified:** `pyproject.toml`
- **Verification:** `pip install -e .` succeeded
- **Committed in:** `07118f4` (Task 1 commit)

**2. [Rule 1 - Bug] Two CLI test assertions corrected**
- **Found during:** Task 8 (CLI tests)
- **Issue:** (a) Click group exits with code 2 when called with no args; (b) `platforms` command shows human-readable descriptions not raw platform keys
- **Fix:** Updated assertions to match actual Click behavior
- **Files modified:** `tests/test_cli.py`
- **Verification:** All 17 CLI tests pass
- **Committed in:** `1286f41` (Task 8 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Both were minor corrections. No scope changes.

## Issues Encountered

None beyond the two auto-fixed bugs above.

## Known Stubs

- `content_downloader/adapters/stub.py` — StubAdapter raises `NotImplementedError` for douyin, xhs, wechat_oa, x. This is intentional: real adapters are Phase 2+ work (ADAPT-01 through ADAPT-04). The stub allows the router and CLI to list all platforms without crashing.

## Next Phase Readiness

- All Phase 2 adapters can drop into `content_downloader/adapters/{platform}.py` and register in `router.py:get_adapter()`
- ContentItem model is the contract — adapters just need to return one
- ManifestManager and OutputManager are ready to accept items from any adapter
- The fixture adapter provides a reference implementation pattern

---
*Phase: 01-scaffold-core*
*Completed: 2026-03-29*

## Self-Check: PASSED

All 9 task commits verified present. All 16 key files exist on disk.
116 tests passing, 93% coverage confirmed.
