<div align="center">

# content-downloader

**给一个 URL，拿回标准化的本地文件 -- 不管是哪个平台、什么内容类型，输出格式完全一致**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-303_passed-brightgreen.svg)](#)
[![Coverage](https://img.shields.io/badge/coverage-85%25-yellowgreen.svg)](#)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/zinan92/content-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/zinan92/content-downloader/actions/workflows/ci.yml)

</div>

---

```
in  URL (douyin | xhs | wechat-oa | x) -- 内容页 or profile 页
out media files + metadata.json + content_item.json + text.txt + manifest.jsonl

fail unsupported platform     -> error + supported list
fail auth required (douyin)   -> "prepare cookies.json" instructions
fail sidecar not running (xhs)-> auto-install + auto-start XHS-Downloader
fail tool missing (x)         -> yt-dlp auto-installed via pip
fail single item in batch     -> skip + continue, error logged in manifest
fail content deleted/private  -> skip + report in result
```

Adapters: douyin, xhs (via XHS-Downloader sidecar), wechat-oa, x (via yt-dlp)

## 示例输出

```
$ python3 -m content_downloader download "https://www.douyin.com/video/7621048932151414054" --cookies cookies.json

Downloaded: 7621048932151414054
  Platform : douyin
  Type     : video
  Location : output/douyin/102174692353/7621048932151414054
```

输出目录结构（每个平台一致）：

```
output/douyin/102174692353/7621048932151414054/
├── media/
│   ├── video.mp4          # 去水印视频
│   └── cover.jpg          # 封面图
├── metadata.json          # 平台原始 API 数据（完整保留）
├── content_item.json      # 标准化 ContentItem（跨平台统一字段）
└── text.txt               # 纯文字内容（视频描述/推文文本/文章标题）

output/manifest.jsonl      # 全局索引，一行一个 item，append-only
```

`content_item.json` 示例：
```json
{
  "platform": "douyin",
  "content_id": "7621048932151414054",
  "content_type": "video",
  "title": "AI 时代的内容创作方法论",
  "description": "分享我的内容创作工作流...",
  "author_id": "102174692353",
  "author_name": "慢学AI",
  "publish_time": "2026-03-30T01:44:29Z",
  "source_url": "https://www.douyin.com/video/7621048932151414054",
  "media_files": ["media/video.mp4"],
  "cover_file": "media/cover.jpg",
  "likes": 38000,
  "comments": 1220,
  "shares": 10000,
  "collects": 31000,
  "views": 520000
}
```

## 架构

```
                        ┌─────────────────────┐
                        │     CLI / API        │
                        │  content-downloader  │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    URL Router        │
                        │  auto-detect platform│
                        └──┬───┬───┬───┬──────┘
                           │   │   │   │
              ┌────────────┘   │   │   └────────────┐
              ▼                ▼   ▼                 ▼
        ┌──────────┐   ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Douyin   │   │   XHS    │ │ WeChat   │ │    X     │
        │ Adapter   │   │ Adapter  │ │ Adapter  │ │ Adapter  │
        │           │   │          │ │          │ │          │
        │ XBogus    │   │ HTTP API │ │ HTML GET │ │ yt-dlp   │
        │ signing   │   │ sidecar  │ │ + parse  │ │ subprocess│
        └─────┬─────┘   └────┬─────┘ └────┬─────┘ └────┬─────┘
              │               │            │             │
              └───────────────┴────────┬───┴─────────────┘
                                       ▼
                            ┌──────────────────┐
                            │  Output Manager   │
                            │  + Manifest JSONL  │
                            └──────────────────┘
                                       ▼
                            ┌──────────────────┐
                            │  Standardized     │
                            │  ContentItem      │
                            │  + media files    │
                            └──────────────────┘
```

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/zinan92/content-downloader.git
cd content-downloader

# 2. 安装（自动安装所有依赖，包括 yt-dlp）
pip install -e .

# 3. 下载内容
# 公众号（零配置，直接可用）
python3 -m content_downloader download "https://mp.weixin.qq.com/s/xxx"

# 抖音（需要 cookies）
python3 -m content_downloader download "https://www.douyin.com/video/xxx" --cookies cookies.json

# 小红书（自动安装并启动 XHS-Downloader）
python3 -m content_downloader download "https://www.xiaohongshu.com/explore/xxx"

# X/Twitter（yt-dlp 已自动安装）
python3 -m content_downloader download "https://x.com/user/status/xxx"

# 创作者主页批量下载（抖音支持）
python3 -m content_downloader download "https://www.douyin.com/user/MS4wLjABAAAAxxx" --limit 5

# 查看支持的平台
python3 -m content_downloader platforms
```

## 功能一览

| 功能 | 说明 | 状态 |
|------|------|------|
| 抖音视频下载 | 去水印 + 封面 + metadata | 已完成 |
| 抖音图文下载 | 多图 + 封面 + metadata | 已完成 |
| 抖音 Profile 批量 | limit/since 增量下载 | 已完成 |
| 抖音短链接 | v.douyin.com 自动解析 | 已完成 |
| 小红书视频 | 通过 XHS-Downloader API | 已完成 |
| 小红书图文 | 多图下载 + cover | 已完成 |
| 小红书 sidecar 自管理 | 自动安装 + 启动 | 已完成 |
| 公众号文章 | HTML + 图片 + 音频 ID | 已完成 |
| X 视频推文 | 视频 + 缩略图 + metadata | 已完成 |
| X 图片推文 | 多图全保留 | 已完成 |
| X 纯文字推文 | metadata + text.txt | 已完成 |
| 统一 ContentItem | 跨平台标准化数据模型 | 已完成 |
| manifest.jsonl | 全局 append-only 索引 | 已完成 |
| 去重 | 已下载 content_id 自动跳过 | 已完成 |
| text.txt | 每条内容附带纯文本文件 | 已完成 |

## 各平台支持的内容类型

| 平台 | 视频 | 图文/多图 | 纯文字/文章 | Profile 批量 |
|------|------|----------|-----------|-------------|
| **抖音** | 去水印 MP4 | 多图 + cover | N/A | --limit N / --since DATE |
| **小红书** | MP4 | 多图 + cover | N/A | 暂不支持 |
| **公众号** | N/A | 文章 HTML + 内嵌图片 | 完整文章 | 暂不支持 |
| **X** | MP4 | 多图全保留 | text.txt | 暂不支持 |

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 语言 | Python 3.11+ | 核心 |
| HTTP | httpx | 异步请求 |
| 数据模型 | Pydantic v2 | ContentItem 校验 |
| CLI | Click | 命令行界面 |
| 抖音签名 | XBogus / ABogus + gmssl | API 请求签名 |
| 小红书 | XHS-Downloader (sidecar) | HTTP API 调用 |
| X/Twitter | yt-dlp | 媒体下载 |
| 测试 | pytest + pytest-asyncio | 303 tests, 85% coverage |

## 项目结构

```
content-downloader/
├── content_downloader/
│   ├── __init__.py
│   ├── __main__.py          # python -m content_downloader
│   ├── cli.py               # CLI: download / list / platforms
│   ├── models.py            # ContentItem, DownloadResult, DownloadError
│   ├── router.py            # URL -> platform 识别 + adapter 路由
│   ├── output.py            # 标准化目录结构写入
│   ├── manifest.py          # JSONL manifest 读写 (file-locked)
│   └── adapters/
│       ├── base.py          # PlatformAdapter protocol
│       ├── fixture.py       # 测试用 fixture adapter
│       ├── douyin/          # 抖音 (XBogus 签名 + API)
│       ├── xhs/             # 小红书 (XHS-Downloader sidecar)
│       ├── wechat_oa/       # 公众号 (HTML 解析)
│       └── x/               # X/Twitter (yt-dlp)
├── tests/                   # 303 tests
├── cookies.json.example     # 抖音 cookies 模板
└── pyproject.toml
```

## 配置

### 抖音 Cookies

抖音需要浏览器 cookies 进行 API 签名。从 Chrome DevTools 导出：

1. 打开 `douyin.com`，确认已登录
2. F12 -> Console -> 输入 `document.cookie` -> 复制
3. 保存为 `cookies.json`（或用 Cookie Editor 导出 Netscape 格式）

```bash
python3 -m content_downloader download "https://www.douyin.com/video/xxx" --cookies cookies.json
```

> Cookies 约 7 天有效，过期后重新导出。

### CLI 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output-dir` | 输出目录 | `./output` |
| `--cookies` | Cookies JSON 文件路径 | 无 |
| `--limit` | Profile 批量下载数量限制 | 0 (全部) |
| `--since` | 增量下载起始日期 (YYYY-MM-DD) | 无 |
| `--force` | 强制重新下载已存在的内容 | False |

## For AI Agents

本节面向需要将此项目作为工具或依赖集成的 AI Agent。

### Capability Contract

```yaml
name: content-downloader
version: 0.1.0
capability:
  summary: Download content from any supported platform into standardized local files
  in: URL (douyin | xhs | wechat-oa | x) — content page or profile page
  out: media files + metadata.json + content_item.json + text.txt + manifest.jsonl
  fail:
    - "unsupported platform -> error + supported list"
    - "auth required (douyin) -> cookies instructions"
    - "sidecar unavailable (xhs) -> auto-install + auto-start"
    - "content deleted/private -> skip + report"
  adapters: [douyin, xhs, wechat_oa, x]
cli_command: python3 -m content_downloader
cli_args:
  - name: url
    type: string
    required: true
    description: Content or profile URL from any supported platform
cli_flags:
  - name: --output-dir
    type: string
    description: Output directory (default ./output)
  - name: --cookies
    type: string
    description: Path to cookies JSON file (required for douyin)
  - name: --limit
    type: integer
    description: Max items for profile download (0 = all)
  - name: --force
    type: boolean
    description: Force re-download even if already exists
install_command: pip install -e .
start_command: python3 -m content_downloader download <url>
```

### Agent 调用示例

```python
import subprocess
import json

# 下载抖音视频
result = subprocess.run(
    ["python3", "-m", "content_downloader", "download",
     "https://www.douyin.com/video/7621048932151414054",
     "--cookies", "cookies.json",
     "--output-dir", "./output"],
    capture_output=True, text=True,
)

# 读取标准化输出
content_item = json.loads(
    open("output/douyin/102174692353/7621048932151414054/content_item.json").read()
)
print(f"Title: {content_item['title']}")
print(f"Media: {content_item['media_files']}")
print(f"Likes: {content_item['likes']}")

# 读取全局 manifest
with open("output/manifest.jsonl") as f:
    for line in f:
        item = json.loads(line)
        print(f"{item['platform']}/{item['content_id']}: {item['title'][:50]}")
```

## 相关项目

| 项目 | 说明 | 链接 |
|------|------|------|
| content-workbench | 内容跨平台分发工作台 (content-downloader 的前端) | [zinan92/content-workbench](https://github.com/zinan92/content-workbench) |
| douyin-downloader-1 | 抖音 adapter 的能力来源 | [zinan92/douyin-downloader-1](https://github.com/zinan92/douyin-downloader-1) |
| XHS-Downloader | 小红书 adapter 的 sidecar 后端 | [JoeanAmier/XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) |
| intelligence | 社交内容趋势研究引擎 (下游消费者) | [zinan92/intelligence](https://github.com/zinan92/intelligence) |
| content-intelligence | 内容洞察引擎 (下游消费者) | [zinan92/content-intelligence](https://github.com/zinan92/content-intelligence) |

## License

MIT License. See [LICENSE](LICENSE) for details.
