# Phase 4: WeChat OA Adapter

**Goal:** 公众号文章下载可用

**Requirements:** ADAPT-07

**Success Criteria:**
- `python -m content_downloader download "https://mp.weixin.qq.com/s/xxx"` 下载文章 HTML + 图片 + 音频
- metadata 包含标题、作者、发布时间
- 输出 ContentItem 格式一致
- 所有测试通过

---

## Task Breakdown

### Task 1: WeChat OA article parser
**Req:** ADAPT-07
**Files:**
- `content_downloader/adapters/wechat_oa/__init__.py`
- `content_downloader/adapters/wechat_oa/parser.py`

**Logic:**
公众号文章是公开 HTML 页面，零反爬风险。

```python
class WeChatOAParser:
    async def fetch_article(self, url: str) -> dict:
        """GET 文章页面，解析 HTML 提取结构化数据"""
        resp = await httpx.AsyncClient().get(url, follow_redirects=True)
        html = resp.text
        return {
            "title": _extract_title(html),         # <h1> 或 meta og:title
            "author": _extract_author(html),        # <span id="js_name">
            "publish_time": _extract_time(html),    # <em id="publish_time">
            "content_html": _extract_body(html),    # <div id="js_content">
            "images": _extract_images(html),        # <img data-src="..."> URLs
            "audio_urls": _extract_audio(html),     # <mpvoice> 或 audio 标签
            "source_url": url,
        }
```

**HTML 解析要点：**
- 标题: `<h1 class="rich_media_title">` 或 `<meta property="og:title">`
- 作者: `<span class="rich_media_meta_text">` 或 `<a id="js_name">`
- 发布时间: `<em id="publish_time">` 或 `var ct = "xxx"` 在 script 中
- 正文: `<div class="rich_media_content" id="js_content">`
- 图片: `data-src` 属性（微信 lazy-load），不是 `src`
- 音频: `<mpvoice>` 标签的 `voice_encode_fileid` 属性

**依赖：** 只需 httpx（已有）+ 标准库 html.parser 或 re。不引入 BeautifulSoup — 公众号 HTML 结构固定，正则足够。

**Done when:** Parser 从 sample HTML 提取出所有字段，单元测试通过

### Task 2: WeChat OA adapter
**Req:** ADAPT-07
**Files:**
- `content_downloader/adapters/wechat_oa/adapter.py`

**Flow:**
1. `can_handle(url)` — 匹配 `mp.weixin.qq.com/s/*`
2. `download_single(url, output_dir)`:
   - 调用 `parser.fetch_article(url)`
   - 保存文章 HTML 到 `media/article.html`
   - 下载所有图片到 `media/img_01.jpg`, `img_02.jpg`, ...
   - 下载音频（如有）到 `media/audio_01.mp3`, ...
   - 保存原始解析结果到 `metadata.json`
   - 映射到 ContentItem:
     ```python
     ContentItem(
         platform="wechat_oa",
         content_id=_extract_article_id(url),  # URL 中的 hash 或 mid
         content_type="article",
         title=parsed["title"],
         description=parsed["content_html"][:200],  # 前 200 字摘要
         author_id=parsed["author"],  # 公众号名称作为 ID
         author_name=parsed["author"],
         publish_time=parsed["publish_time"],
         source_url=url,
         media_files=["media/article.html"] + img_files + audio_files,
         cover_file=img_files[0] if img_files else None,
         metadata_file="metadata.json",
         likes=0, comments=0, shares=0, collects=0, views=0,  # 公众号不公开互动数据
     )
     ```
3. `download_profile` — 不支持（公众号没有公开的文章列表页），返回 unsupported + workaround

**Done when:** Mock HTML → 完整目录结构输出

### Task 3: Register + tests
**Files:**
- 更新 `content_downloader/router.py` — 注册 WeChatOAAdapter
- `tests/adapters/wechat_oa/test_parser.py` — HTML 解析测试
- `tests/adapters/wechat_oa/test_adapter.py` — 下载流程测试
- `tests/adapters/wechat_oa/fixtures/sample_article.html` — 样例 HTML

**Done when:** 所有测试通过，router 正确路由 mp.weixin.qq.com URLs

---

## Build Order

```
Task 1 (Parser) → Task 2 (Adapter) → Task 3 (Register + Tests)
```

## Verification Checklist

- [ ] `python -m content_downloader platforms` 显示 wechat_oa [ready]
- [ ] Mock 测试：文章 HTML → title/author/time/images 正确提取
- [ ] Mock 测试：download_single → article.html + images + content_item.json
- [ ] Mock 测试：download_profile → unsupported error
- [ ] ContentItem content_type = "article"
- [ ] manifest.jsonl 正确追加 wechat_oa items
