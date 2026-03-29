# Phase 5: X Adapter

**Goal:** X/Twitter 媒体下载可用

**Requirements:** ADAPT-08

**Success Criteria:**
- `python -m content_downloader download "https://x.com/user/status/xxx"` 下载图片/视频 + metadata
- metadata 包含推文文本、engagement metrics
- 输出 ContentItem 格式一致
- 所有测试通过

---

## Task Breakdown

### Task 1: X content fetcher via yt-dlp
**Req:** ADAPT-08
**Files:**
- `content_downloader/adapters/x/__init__.py`
- `content_downloader/adapters/x/fetcher.py`

**策略：用 yt-dlp 作为后端**

yt-dlp 已经支持 X/Twitter 下载（视频 + metadata JSON），且不需要 API key。比自己调 X API 更安全、更稳定。

```python
class XFetcher:
    async def fetch_post(self, url: str, output_dir: Path) -> dict:
        """用 yt-dlp 下载推文媒体 + 提取 metadata"""
        # 使用 asyncio.create_subprocess_exec（非 shell，安全）
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--write-info-json",
            "--write-thumbnail",
            "--no-playlist",
            "-o", str(output_dir / "media" / "%(id)s.%(ext)s"),
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # 解析 .info.json 获取 metadata
        info_json = _find_info_json(output_dir / "media")
        return json.loads(info_json.read_text())

    async def is_available(self) -> bool:
        """检查 yt-dlp 是否安装"""
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
        return proc.returncode == 0
```

**NOTE:** 使用 `create_subprocess_exec`（非 shell），避免命令注入。URL 作为参数传入，不拼接到 shell 命令。

**yt-dlp info.json 关键字段：**
- `id` → content_id
- `title` / `description` → title / description
- `uploader` → author_name
- `uploader_id` → author_id
- `timestamp` → publish_time
- `like_count`, `repost_count`, `comment_count` → engagement
- `view_count` → views
- `webpage_url` → source_url

**依赖：** yt-dlp 作为外部 CLI 工具（pip install yt-dlp 或 brew install），不作为 Python 库导入

**Done when:** yt-dlp wrapper 能提取 metadata dict（mock subprocess 测试）

### Task 2: X adapter
**Req:** ADAPT-08
**Files:**
- `content_downloader/adapters/x/adapter.py`
- `content_downloader/adapters/x/mapper.py`

**Flow:**
1. `can_handle(url)` — 匹配 `x.com/*/status/*` 和 `twitter.com/*/status/*`
2. `download_single(url, output_dir)`:
   - 检查 yt-dlp 是否可用
   - 如不可用 → raise error + "Install yt-dlp: pip install yt-dlp"
   - 调用 `fetcher.fetch_post(url, output_dir)`
   - 处理纯文本推文（无媒体）→ 只保存 metadata，media_files = []
   - 映射到 ContentItem:
     ```python
     ContentItem(
         platform="x",
         content_id=info["id"],
         content_type="video" if has_video else "image" if has_images else "text",
         title=info.get("title", "")[:100],
         description=info.get("description", ""),
         author_id=info.get("uploader_id", ""),
         author_name=info.get("uploader", ""),
         publish_time=datetime.fromtimestamp(info["timestamp"]).isoformat(),
         source_url=info.get("webpage_url", url),
         media_files=downloaded_files,
         cover_file=thumbnail_file,
         metadata_file="metadata.json",
         likes=info.get("like_count", 0),
         comments=info.get("comment_count", 0),
         shares=info.get("repost_count", 0),
         collects=0,  # X bookmark count not public
         views=info.get("view_count", 0),
     )
     ```
3. `download_profile` — 不支持（yt-dlp 不支持批量下载用户时间线），返回 unsupported

**Done when:** Mock subprocess → 完整目录结构输出

### Task 3: Register + tests
**Files:**
- 更新 `content_downloader/router.py` — 注册 XAdapter
- `tests/adapters/x/test_fetcher.py` — mock subprocess
- `tests/adapters/x/test_adapter.py` — 下载流程测试
- `tests/adapters/x/test_mapper.py` — info.json → ContentItem 映射
- `tests/adapters/x/fixtures/sample_info.json` — 样例 yt-dlp output

**Done when:** 所有测试通过，router 正确路由 x.com / twitter.com URLs

---

## Build Order

```
Task 1 (Fetcher) → Task 2 (Adapter) → Task 3 (Register + Tests)
```

## Verification Checklist

- [ ] `python -m content_downloader platforms` 显示 x [ready]
- [ ] Mock 测试：yt-dlp subprocess → 正确解析 info.json
- [ ] Mock 测试：download_single 视频推文 → video + content_item.json
- [ ] Mock 测试：download_single 图片推文 → images + content_item.json
- [ ] Mock 测试：download_single 纯文本 → metadata only
- [ ] Mock 测试：yt-dlp 不可用 → 清晰安装指引
- [ ] Mock 测试：download_profile → unsupported error
- [ ] x.com 和 twitter.com 两种 URL 都能路由
- [ ] manifest.jsonl 正确追加 x items
