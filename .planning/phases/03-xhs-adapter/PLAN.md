# Phase 3: XHS Adapter

**Goal:** XHS-Downloader HTTP API 集成，小红书笔记下载可用

**Requirements:** ADAPT-04, ADAPT-05, ADAPT-06

**Success Criteria:**
- `python -m content_downloader download "https://www.xiaohongshu.com/explore/xxx"` 下载图片/视频 + metadata
- `python -m content_downloader download "https://www.xiaohongshu.com/user/profile/xxx" --limit 10` 批量下载
- XHS-Downloader sidecar 检测（运行中直接调用，未运行给出启动指引）
- 输出目录结构和 ContentItem 格式与 douyin/fixture adapter 完全一致
- 所有 XHS adapter 单元测试通过

**Integration:** 通过 HTTP API 调用 XHS-Downloader（sidecar 模式），不嵌入 XHS-Downloader 代码

---

## Task Breakdown

### Task 1: XHS-Downloader HTTP API client
**Req:** ADAPT-06
**Files:**
- `content_downloader/adapters/xhs/__init__.py`
- `content_downloader/adapters/xhs/api_client.py`

**XHS-Downloader API 接口（FastAPI, port 5556）：**
- `POST /xhs/detail` — 获取笔记详情 + 下载地址
  - Body: `{"url": "...", "download": false, "index": "", "skip": false}`
  - Returns: 笔记完整数据（标题、描述、图片 URL 列表、视频 URL、互动数据、作者信息）
- Health check: `GET /` 或连接测试

**Client 实现：**
```python
class XHSAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:5556"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_note_detail(self, url: str) -> dict:
        """获取单条笔记详情"""
        resp = await self.client.post(f"{self.base_url}/xhs/detail",
            json={"url": url, "download": False, "skip": False})
        return resp.json()

    async def is_available(self) -> bool:
        """检查 XHS-Downloader 是否运行"""
        try:
            resp = await self.client.get(self.base_url, timeout=3.0)
            return resp.status_code == 200
        except httpx.ConnectError:
            return False
```

**Done when:** API client 可独立调用，mock 测试通过

### Task 2: XHS note detail → ContentItem mapper
**Req:** ADAPT-04
**Files:**
- `content_downloader/adapters/xhs/mapper.py`

**映射逻辑（XHS API response → ContentItem）：**
```python
ContentItem(
    platform="xhs",
    content_id=note_data.get("note_id") or note_data.get("id"),
    content_type="gallery" if note_data.get("type") == "normal" else "video",
    title=note_data.get("title", ""),
    description=note_data.get("desc", ""),
    author_id=note_data.get("user_id", ""),
    author_name=note_data.get("nickname", ""),
    publish_time=_parse_xhs_time(note_data.get("time")),  # ms timestamp
    source_url=note_data.get("note_url", url),
    media_files=[...],  # 下载后的相对路径列表
    cover_file="media/cover.jpg" if has_cover else None,
    metadata_file="metadata.json",
    likes=int(note_data.get("liked_count", 0)),
    comments=int(note_data.get("comment_count", 0)),
    shares=int(note_data.get("share_count", 0)),
    collects=int(note_data.get("collected_count", 0)),
    views=0,  # XHS 不公开展示播放量
)
```

**图片 vs 视频处理：**
- `type == "normal"` → 图文笔记 → 下载 image_list 里所有图片
- `type == "video"` → 视频笔记 → 下载 video_url

**Done when:** Mapper 单元测试覆盖图文笔记和视频笔记两种类型

### Task 3: XHS adapter — download_single
**Req:** ADAPT-04
**Files:**
- `content_downloader/adapters/xhs/adapter.py`

**Flow:**
1. `can_handle(url)` — 匹配 xiaohongshu.com/explore/*, xiaohongshu.com/discovery/*, xhslink.com/*
2. `download_single(url, output_dir)`:
   - 检查 XHS-Downloader 是否可用（`is_available()`）
   - 如不可用 → raise `DownloadError(error_type="service_unavailable", message="XHS-Downloader not running. Start it with: python main.py api")`
   - 调用 `api_client.get_note_detail(url)`
   - 如返回空 dict → raise `DownloadError(error_type="not_found")`
   - 解析返回数据，确定图文/视频类型
   - 下载所有媒体文件到 `output_dir/media/`
     - 图文：`img_01.jpg`, `img_02.jpg`, ...
     - 视频：`video.mp4`
   - 保存原始 API response 到 `metadata.json`
   - 映射到 ContentItem，保存 `content_item.json`

**Done when:** Mock 测试覆盖图文和视频两种笔记

### Task 4: XHS adapter — download_profile
**Req:** ADAPT-05
**Files:**
- 扩展 `content_downloader/adapters/xhs/adapter.py`

**Profile 下载策略：**

XHS-Downloader 的 API 可能不直接支持 profile 批量获取（它主要是单条笔记 API）。两种策略：

**策略 A（如果 API 支持）：** 直接调用 profile endpoint

**策略 B（fallback，更可能）：**
1. 提取 user_id from profile URL
2. 使用 XHS-Downloader 的 profile/creator 功能（如果 API 暴露）
3. 如果 API 不支持 → 返回 `DownloadError(error_type="unsupported", message="Profile batch download requires XHS-Downloader creator mode. Use CLI: python main.py --type creator")`

**实现决策：**
- 先实现 download_single 完整可用
- download_profile 先返回 unsupported error 并附带 workaround 指引
- 后续版本可通过 XHS-Downloader 的 TUI/CLI 模式补充

**Done when:** download_profile 返回清晰的 unsupported error + workaround

### Task 5: Sidecar health check + error guidance
**Req:** ADAPT-06
**Files:**
- `content_downloader/adapters/xhs/sidecar.py`

**职责：**
```python
class XHSSidecar:
    async def check_health(self) -> bool:
        """检查 XHS-Downloader 是否在运行"""

    def get_start_instructions(self) -> str:
        """返回启动 XHS-Downloader 的指引"""
        return (
            "XHS-Downloader is not running.\n"
            "Start it with:\n"
            "  cd /path/to/XHS-Downloader\n"
            "  python main.py api\n"
            "It will start on http://127.0.0.1:5556"
        )
```

**CLI 集成：**
- 下载前先 check health
- 不可用时打印清晰的启动指引，不是 cryptic error

**Done when:** 不可用时 CLI 输出友好的启动指引

### Task 6: Register adapter in router
**Files:**
- 更新 `content_downloader/router.py` — 注册 XHSAdapter
- 确保 URL 分类覆盖所有 XHS URL 格式

**XHS URL patterns:**
- `xiaohongshu.com/explore/{note_id}` → single
- `xiaohongshu.com/discovery/item/{note_id}` → single
- `xhslink.com/{short_code}` → single (短链接)
- `xiaohongshu.com/user/profile/{user_id}` → profile

**Done when:** `python -m content_downloader platforms` 显示 xhs [ready]

### Task 7: Unit tests
**Req:** All ADAPT-04~06
**Files:**
- `tests/adapters/xhs/test_api_client.py` — mock HTTP responses
- `tests/adapters/xhs/test_adapter.py` — download_single (图文 + 视频)
- `tests/adapters/xhs/test_mapper.py` — note → ContentItem 映射
- `tests/adapters/xhs/test_sidecar.py` — health check + error guidance
- `tests/adapters/xhs/fixtures/` — sample API response JSONs

**测试策略：**
- 全部 mock HTTP — 模拟 XHS-Downloader API 响应
- 覆盖：图文笔记（多图）、视频笔记、API 不可用、空结果、profile unsupported
- 验证 ContentItem 字段完整性

**Done when:** 所有 XHS adapter 测试通过，覆盖率 >85%

---

## Build Order

```
Task 1 (API Client) → Task 2 (Mapper) → Task 3 (download_single) → Task 4 (download_profile)
                    → Task 5 (Sidecar)
                    → Task 6 (Router)
All → Task 7 (Tests)
```

**Critical path:** 1 → 2 → 3 → 7

---

## Verification Checklist

- [ ] `pip install -e .` 成功
- [ ] `python -m content_downloader platforms` 显示 xhs [ready]
- [ ] XHSAdapter.can_handle() 匹配所有 XHS URL 格式
- [ ] Mock 测试：download_single 图文笔记 → 多张图片 + content_item.json
- [ ] Mock 测试：download_single 视频笔记 → video.mp4 + content_item.json
- [ ] Mock 测试：XHS-Downloader 不可用 → 清晰的启动指引
- [ ] Mock 测试：API 返回空 → DownloadError(not_found)
- [ ] Mock 测试：download_profile → unsupported error + workaround
- [ ] ContentItem 字段完整：likes/comments/shares/collects 有值
- [ ] manifest.jsonl 正确追加 xhs items
- [ ] 所有测试通过，覆盖率 >85%
