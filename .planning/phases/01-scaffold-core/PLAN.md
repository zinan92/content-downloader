# Phase 1: Scaffold + Core

**Goal:** CLI 骨架 + adapter 接口 + ContentItem 模型 + manifest + fixture adapter 完整跑通

**Requirements:** CORE-01~07, TEST-01~04, SAFE-01~04

**Success Criteria:**
- `python -m content_downloader download "https://fixture.test/video/123"` → 标准目录结构
- `python -m content_downloader download "https://fixture.test/user/abc" --limit 3` → 3 个 item
- `manifest.jsonl` 正确追加
- `content_item.json` schema 验证通过
- 全部测试通过，覆盖率 >80%

---

## Task Breakdown

### Task 1: Project scaffold
**Req:** Foundation
**Files:**
- `pyproject.toml` — Python 3.11+, dependencies (click, httpx, pydantic)
- `.gitignore` — Python, IDE, output/
- `content_downloader/__init__.py`
- `content_downloader/__main__.py` — `python -m content_downloader` entry
- `tests/__init__.py`
- `tests/conftest.py` — shared fixtures

**Done when:** `pip install -e .` succeeds, `python -m content_downloader --help` prints help

### Task 2: Data models
**Req:** CORE-05, CORE-07
**Files:**
- `content_downloader/models.py`

**Models (frozen dataclasses or Pydantic):**
```python
class ContentItem:
    platform: str              # "douyin" | "xhs" | "wechat_oa" | "x" | "fixture"
    content_id: str            # 平台原始 ID
    content_type: str          # "video" | "image" | "article" | "gallery"
    title: str
    description: str
    author_id: str
    author_name: str
    publish_time: str          # ISO 8601
    source_url: str
    media_files: list[str]     # relative paths: ["media/video.mp4"]
    cover_file: str | None     # "media/cover.jpg"
    metadata_file: str         # "metadata.json"
    likes: int
    comments: int
    shares: int
    collects: int
    views: int
    downloaded_at: str         # ISO 8601

class DownloadError:
    content_id: str
    source_url: str
    error_type: str            # "auth" | "rate_limit" | "not_found" | "network" | "unsupported"
    message: str
    retryable: bool

class DownloadResult:
    items: list[ContentItem]
    errors: list[DownloadError]
    total: int
    success: int
    failed: int
    skipped: int
```

**Done when:** `tests/test_models.py` passes — JSON round-trip, field validation

### Task 3: Platform adapter interface
**Req:** CORE-01, TEST-01
**Files:**
- `content_downloader/adapters/__init__.py`
- `content_downloader/adapters/base.py`

**Interface:**
```python
class PlatformAdapter(Protocol):
    platform: str

    async def download_single(
        self, url: str, output_dir: Path
    ) -> ContentItem: ...

    async def download_profile(
        self, profile_url: str, output_dir: Path,
        limit: int = 0,
        since: datetime | None = None,
    ) -> DownloadResult: ...

    def can_handle(self, url: str) -> bool: ...
```

**Done when:** Protocol defined, importable, type-checkable

### Task 4: Fixture adapter
**Req:** TEST-01
**Files:**
- `content_downloader/adapters/fixture.py`
- `tests/test_fixture_adapter.py`

**Behavior:**
- `can_handle("https://fixture.test/...")` → True
- `download_single` → creates standard directory structure with dummy files
- `download_profile` → creates N items (respects `limit`)
- Writes real files to disk (small dummy media, valid JSON metadata)
- Deterministic output for testing

**Done when:** Fixture adapter produces full output directory structure, tests pass

### Task 5: URL router
**Req:** CORE-01, SAFE-03
**Files:**
- `content_downloader/router.py`
- `tests/test_router.py`

**Logic:**
```python
def classify_url(url: str) -> tuple[str, str]:
    """Returns (platform, url_type) where url_type is 'single' | 'profile'"""

def get_adapter(url: str) -> PlatformAdapter:
    """Routes URL to the correct adapter. Raises UnsupportedPlatformError if no match."""
```

**URL patterns to recognize:**
- `douyin.com/video/*`, `v.douyin.com/*` → douyin/single
- `douyin.com/user/*` → douyin/profile
- `xiaohongshu.com/explore/*`, `xiaohongshu.com/discovery/*`, `xhslink.com/*` → xhs/single
- `xiaohongshu.com/user/profile/*` → xhs/profile
- `mp.weixin.qq.com/s/*` → wechat_oa/single
- `x.com/*/status/*`, `twitter.com/*/status/*` → x/single
- `fixture.test/*` → fixture (testing)

**Done when:** All URL patterns tested, unsupported URLs raise clear error with supported list

### Task 6: Output manager
**Req:** CORE-04, CORE-05
**Files:**
- `content_downloader/output.py`
- `tests/test_output.py`

**Responsibilities:**
- Create `output/{platform}/{author_id}/{content_id}/` directory
- Create `media/` subdirectory
- Write `metadata.json` (platform raw data)
- Write `content_item.json` (standardized ContentItem)
- Return paths to caller

**Done when:** Given a ContentItem + raw metadata dict, creates full directory structure

### Task 7: Manifest manager
**Req:** CORE-06, SAFE-04, TEST-04
**Files:**
- `content_downloader/manifest.py`
- `tests/test_manifest.py`

**Responsibilities:**
- Append ContentItem summary to `manifest.jsonl` (file-locked)
- Check if content_id already exists (dedup)
- Read manifest for listing/querying

**Done when:** Concurrent append test passes, dedup works, JSONL format valid

### Task 8: CLI entry point
**Req:** CORE-01, CORE-02, CORE-03, SAFE-01, SAFE-02
**Files:**
- `content_downloader/cli.py`
- `tests/test_cli.py`

**Commands:**
```bash
# Download single URL
content-downloader download <url> [--output-dir ./output] [--force]

# Download from profile
content-downloader download <profile-url> --limit 10 --since 2026-03-01

# List downloaded items
content-downloader list [--platform douyin] [--output-dir ./output]

# Show supported platforms
content-downloader platforms
```

**Config (optional, via `--config`):**
```yaml
output_dir: ./output
rate_limit:
  min_delay: 1.0
  max_delay: 3.0
cookies:
  douyin: "cookie_string"
  xhs: "cookie_string"
```

**Done when:** `python -m content_downloader download "https://fixture.test/video/123"` produces full output

### Task 9: Integration test — full flow
**Req:** All CORE + SAFE + TEST
**Files:**
- `tests/test_integration.py`

**Test scenarios:**
1. Single URL → download → verify directory structure + manifest
2. Profile URL with --limit → download N items → verify count + manifest
3. Duplicate URL → skip + report
4. Unsupported URL → clear error message
5. --force flag → re-download even if exists

**Done when:** All integration tests pass, fixture adapter exercised end-to-end

---

## Build Order

```
Task 1 (Scaffold) → Task 2 (Models) → Task 3 (Adapter Interface)
                                    → Task 5 (Router)
                  → Task 6 (Output Manager)
                  → Task 7 (Manifest Manager)

Task 4 (Fixture Adapter) depends on: Task 2, 3, 6
Task 8 (CLI) depends on: Task 2, 3, 4, 5, 6, 7
Task 9 (Integration) depends on: all above
```

**Parallelizable:** Tasks 2+5+6+7 can be developed in parallel after Task 1.

---

## Verification Checklist

- [ ] `pip install -e .` → success
- [ ] `python -m content_downloader --help` → shows commands
- [ ] `python -m content_downloader platforms` → lists fixture + 4 platforms (stubs)
- [ ] `python -m content_downloader download "https://fixture.test/video/abc123"` → output/fixture/test-author/abc123/
- [ ] `output/fixture/test-author/abc123/content_item.json` → valid ContentItem
- [ ] `output/fixture/test-author/abc123/metadata.json` → valid JSON
- [ ] `output/fixture/test-author/abc123/media/video.mp4` → file exists
- [ ] `output/manifest.jsonl` → has 1 line with correct content_id
- [ ] Re-run same command → skipped (dedup)
- [ ] `--force` → re-downloads
- [ ] Profile URL with `--limit 3` → 3 items downloaded
- [ ] Unsupported URL → clear error with supported platforms list
- [ ] `pytest tests/ -v` → all green, >80% coverage
