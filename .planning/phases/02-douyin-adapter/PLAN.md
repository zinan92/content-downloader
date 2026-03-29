# Phase 2: Douyin Adapter

**Goal:** 移植 douyin-downloader-1 核心能力，真实抖音视频下载可用

**Requirements:** ADAPT-01, ADAPT-02, ADAPT-03

**Success Criteria:**
- `python -m content_downloader download "https://www.douyin.com/video/xxx"` 下载去水印视频 + metadata
- `python -m content_downloader download "https://www.douyin.com/user/xxx" --limit 5` 批量下载 5 条
- `https://v.douyin.com/xxx` 短链接自动解析到正确视频
- 输出目录结构和 ContentItem 格式与 fixture adapter 完全一致
- 所有 douyin adapter 单元测试通过

**Source:** 移植自 `/Users/wendy/work/content-co/douyin-downloader-1/`

---

## Task Breakdown

### Task 1: Copy signing and auth utilities
**Req:** Foundation for API calls
**Files:**
- `content_downloader/adapters/douyin/xbogus.py` — 从 `douyin-downloader-1/utils/xbogus.py` 移植
- `content_downloader/adapters/douyin/abogus.py` — 从 `douyin-downloader-1/utils/abogus.py` 移植
- `content_downloader/adapters/douyin/ms_token.py` — 从 `douyin-downloader-1/auth/ms_token_manager.py` 移植
- `content_downloader/adapters/douyin/cookie_manager.py` — 从 `douyin-downloader-1/auth/cookie_manager.py` 移植，简化

**Changes during migration:**
- 移除 Playwright 依赖（不需要浏览器 cookie 抓取）
- 简化 CookieManager：只从 JSON 文件或 dict 加载，不需要交互式获取
- 保持 XBogus/ABogus 签名逻辑完整不改动
- 保持 gmssl SM4 加密依赖

**Done when:** 签名和 token 模块可独立导入，无外部浏览器依赖

### Task 2: API Client
**Req:** ADAPT-01, ADAPT-03
**Files:**
- `content_downloader/adapters/douyin/api_client.py` — 从 `douyin-downloader-1/core/api_client.py` 移植

**保留的方法：**
- `get_video_detail(aweme_id)` — 单条视频元数据
- `get_user_post(sec_uid, max_cursor, count)` — 用户视频列表（分页）
- `resolve_short_url(short_url)` — v.douyin.com 短链接解析
- `sign_url()` / `build_signed_path()` — 请求签名
- `_ensure_ms_token()` — token 管理

**移除的方法：**
- `collect_user_post_ids_via_browser()` — 浏览器 fallback（太重，暂不需要）
- `get_user_like/music/mix/collects` — Phase 2 只支持 post 模式

**变更：**
- 使用 httpx 替代 aiohttp（与 Phase 1 的 httpx 依赖一致）
- 错误处理映射到 DownloadError 模型

**Done when:** `api_client.get_video_detail("test_id")` 能返回结构化数据（mock 测试）

### Task 3: Douyin adapter — download_single
**Req:** ADAPT-01
**Files:**
- `content_downloader/adapters/douyin/__init__.py`
- `content_downloader/adapters/douyin/adapter.py` — 实现 PlatformAdapter
- `content_downloader/adapters/douyin/mapper.py` — aweme_data → ContentItem 映射

**核心逻辑（从 downloader_base.py 移植）：**
1. `can_handle(url)` — 检查 douyin.com / v.douyin.com
2. `download_single(url, output_dir)`:
   - 解析 URL 提取 aweme_id（或解析短链接）
   - 调用 `api_client.get_video_detail(aweme_id)`
   - 从 `video.play_addr.url_list` 提取去水印 URL（优先 watermark=0）
   - 下载视频文件到 `output_dir/media/video.mp4`
   - 下载封面到 `output_dir/media/cover.jpg`
   - 保存原始 API response 到 `metadata.json`
   - 映射到 ContentItem 并保存 `content_item.json`

**Aweme → ContentItem 映射：**
```python
ContentItem(
    platform="douyin",
    content_id=aweme_data["aweme_id"],
    content_type="video",  # or "gallery" for image posts
    title=aweme_data["desc"][:100],
    description=aweme_data["desc"],
    author_id=aweme_data["author"]["uid"],
    author_name=aweme_data["author"]["nickname"],
    publish_time=datetime.fromtimestamp(aweme_data["create_time"]).isoformat(),
    source_url=aweme_data.get("share_url", url),
    media_files=["media/video.mp4"],
    cover_file="media/cover.jpg",
    metadata_file="metadata.json",
    likes=stats.get("digg_count", 0),
    comments=stats.get("comment_count", 0),
    shares=stats.get("share_count", 0),
    collects=stats.get("collect_count", 0),
    views=stats.get("play_count", 0),
)
```

**Done when:** `download_single("https://fixture.test/video/123", tmp_dir)` 产出完整目录（mock API）

### Task 4: Douyin adapter — download_profile
**Req:** ADAPT-02
**Files:**
- 扩展 `content_downloader/adapters/douyin/adapter.py`

**核心逻辑（从 user_downloader.py + post_strategy.py 移植）：**
1. `download_profile(profile_url, output_dir, limit, since)`:
   - 从 URL 提取 sec_uid
   - 循环调用 `api_client.get_user_post(sec_uid, cursor, 20)`
   - 对每条 aweme 调用 `download_single` 逻辑
   - 尊重 `limit` 参数（0 = 全部）
   - 尊重 `since` 参数（跳过 publish_time < since 的）
   - 检测分页停滞（cursor 不推进 + has_more=True → 停止）
   - 收集 DownloadResult

**Done when:** Profile URL 批量下载 mock 测试通过，limit 和 since 参数生效

### Task 5: Short link resolver
**Req:** ADAPT-03
**Files:**
- 扩展 `content_downloader/adapters/douyin/api_client.py`（已有 resolve_short_url）
- 扩展 `content_downloader/adapters/douyin/adapter.py`（download_single 开头检测短链接）

**逻辑：**
```python
if "v.douyin.com" in url:
    resolved = await api_client.resolve_short_url(url)
    # 重新解析 resolved URL 提取 aweme_id
```

**Done when:** `v.douyin.com/xxx` 短链接 → 正确解析 → 正常下载（mock 测试）

### Task 6: Register adapter in router
**Files:**
- 更新 `content_downloader/router.py` — 注册 DouyinAdapter
- 更新 `content_downloader/cli.py` — 添加 `--cookies` 参数支持

**Changes:**
- router 发现 douyin URL 时返回 DouyinAdapter 实例
- CLI 支持 `--cookies path/to/cookies.json` 传递给 adapter

**Done when:** `python -m content_downloader download "https://www.douyin.com/video/xxx"` 走到 douyin adapter

### Task 7: Unit tests
**Req:** All ADAPT-01~03
**Files:**
- `tests/adapters/douyin/test_api_client.py` — mock HTTP responses
- `tests/adapters/douyin/test_adapter.py` — download_single, download_profile
- `tests/adapters/douyin/test_mapper.py` — aweme → ContentItem 映射
- `tests/adapters/douyin/test_short_link.py` — 短链接解析
- `tests/adapters/douyin/fixtures/` — sample API response JSONs

**测试策略：**
- 全部 mock HTTP — 不需要真实网络
- 使用 douyin-downloader-1 的测试 fixtures 作为参考
- 覆盖：正常下载、短链接、profile 分页、limit/since、去水印 URL 选择、API 错误

**Done when:** 所有 douyin adapter 测试通过，覆盖率 >85%

### Task 8: Dependencies update
**Files:**
- `pyproject.toml` — 添加 gmssl（签名需要的 SM4 加密）

**Done when:** `pip install -e .` 成功，所有导入正常

---

## Build Order

```
Task 8 (Dependencies) → Task 1 (Signing/Auth) → Task 2 (API Client) → Task 3 (download_single)
                                                                      → Task 5 (Short link)
                                                 → Task 4 (download_profile)
                      → Task 6 (Router registration)
                      → Task 7 (Tests)
```

**Critical path:** 8 → 1 → 2 → 3 → 7

---

## Migration Notes

**从 douyin-downloader-1 移植的文件：**
- `utils/xbogus.py` → `adapters/douyin/xbogus.py` (照搬)
- `utils/abogus.py` → `adapters/douyin/abogus.py` (照搬)
- `auth/ms_token_manager.py` → `adapters/douyin/ms_token.py` (简化)
- `auth/cookie_manager.py` → `adapters/douyin/cookie_manager.py` (简化，去掉 Playwright)
- `core/api_client.py` → `adapters/douyin/api_client.py` (保留核心方法，httpx 替 aiohttp)
- `core/downloader_base.py` lines 482-510 → `adapters/douyin/adapter.py` (去水印 URL 提取)
- `core/user_modes/post_strategy.py` → `adapters/douyin/adapter.py` (分页逻辑)

**不移植的文件：**
- `core/transcript_*` — 属于 content-extractor
- `core/analysis_manager.py` — 属于 content-extractor
- `core/archive_manager.py` — 属于 content-extractor
- `core/pipeline.py` — 不需要
- `storage/database.py` — 用 manifest.jsonl 替代
- `core/user_modes/like/music/mix_strategy.py` — Phase 2 只需 post

---

## Verification Checklist

- [ ] `pip install -e .` 成功（gmssl 依赖）
- [ ] `python -m content_downloader platforms` 列出 douyin（非 stub）
- [ ] DouyinAdapter.can_handle() 正确匹配所有 douyin URL 格式
- [ ] Mock 测试：download_single 产出正确目录结构
- [ ] Mock 测试：download_profile with limit=3 产出 3 个 item
- [ ] Mock 测试：短链接解析 → 正确 aweme_id
- [ ] Mock 测试：去水印 URL 选择优先 watermark=0
- [ ] ContentItem 字段完整：likes/comments/shares/collects/views 都有值
- [ ] manifest.jsonl 正确追加 douyin items
- [ ] 所有测试通过，覆盖率 >85%
