# content-downloader

## What This Is

统一内容下载器。接收任意支持平台的 URL（内容页或 profile 页），自动识别平台，通过 adapter 模式调用对应下载器，输出标准化的 ContentItem（媒体文件 + metadata.json + content_item.json）。这是 Content Pipeline End-State 的 Step 02 capability。

## Core Value

给一个 URL，拿回标准化的本地文件 — 不管是哪个平台、什么内容类型，输出格式完全一致，下游 capability（content-extractor、content-workbench）可以统一消费。

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] **CORE-01**: CLI 接收 URL，自动识别平台，路由到对应 adapter
- [ ] **CORE-02**: CLI 接收 profile URL，批量下载创作者内容（支持 limit 和 since 增量）
- [ ] **CORE-03**: 统一输出格式 — `output/{platform}/{author_id}/{content_id}/` 包含 media/ + metadata.json + content_item.json
- [ ] **CORE-04**: 全局 manifest.jsonl — append-only 索引，一行一个 ContentItem
- [ ] **CORE-05**: ContentItem 标准化数据模型 — 统一字段名跨所有平台
- [ ] **CORE-06**: 互动数据随下载一起保存 — likes, comments(数量), shares, collects, views
- [ ] **ADAPT-01**: 抖音 adapter — 移植 douyin-downloader-1 核心能力（URL解析 + API + 去水印下载）
- [ ] **ADAPT-02**: 小红书 adapter — 通过 HTTP API 调用 XHS-Downloader（不登录，低风险）
- [ ] **ADAPT-03**: 公众号 adapter — HTTP GET 公开文章 HTML + 提取图片/音频
- [ ] **ADAPT-04**: X adapter — yt-dlp 或官方 API 封装
- [ ] **SAFE-01**: 反爬安全 — 速率控制、请求间隔随机化、不强制登录
- [ ] **SAFE-02**: 失败隔离 — 单条失败不影响批量任务其余条目
- [ ] **TEST-01**: 每个 adapter 独立可测 — fixture 模式 + 真实模式

### Out of Scope

- 评论内容抓取 — 额外 API 请求，反爬风险成倍增加，属于 signal-scanner 的职责
- 语音转录 (Whisper) — 属于 content-extractor (Step 03) 的职责
- Markdown 归档 / 分析摘要 — 属于 content-extractor 的职责
- 内容发布 — 属于 content-publisher (Step 07) 的职责
- Web UI — 纯 CLI/API，UI 由 content-workbench 提供
- 搜索/关键词发现 — 属于 signal-scanner (Step 01) 的职责

## Context

**Content Pipeline End-State 位置：** Step 02 "把原始内容拿到手"

**上游：** signal-scanner (Step 01) 产出 URL 列表，或用户手动输入 URL
**下游：** content-extractor (Step 03) 消费 ContentItem，转录/提取结构化文本

**现有资产：**
- `douyin-downloader-1` — 抖音下载最成熟（71 tests, manifest, SQLite, 去水印），移植核心
- `XHS-Downloader` (JoeanAmier/XHS-Downloader, 10.5k stars) — 小红书专用，有 HTTP API，不需登录
- `MediaCrawler` — 7 平台爬虫，但强制登录、monolith，不用于下载，搜索/评论能力留给 signal-scanner

**反爬策略：**
- 小红书：用 XHS-Downloader（不登录，低风险）而非 MediaCrawler（强制登录，高风险）
- 抖音：Cookie 签名但不要求登录态，内置速率控制
- 公众号：公开 HTML，零风险
- X：官方 API 或 yt-dlp，不涉及个人账号

## Constraints

- **Language**: Python 3.11+ — 与所有现有下载器一致
- **Architecture**: Adapter pattern — 每个平台一个 adapter，共享统一接口
- **Output**: 标准化目录结构 + ContentItem JSON — 下游不需要知道平台差异
- **Safety**: 不强制用户登录任何平台 — 降低封号风险
- **Dependencies**: XHS-Downloader 作为 sidecar 进程（HTTP API），不嵌入代码
- **MECE**: 只负责下载 + metadata，不做转录/分析/发布

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| XHS-Downloader 而非 MediaCrawler 作为 XHS adapter | 不需登录，有 HTTP API，专注下载，10.5k stars | — Pending |
| 评论内容不在 downloader scope | 额外 API 请求增加反爬风险，属于 signal-scanner 职责 | — Pending |
| 转录不在 downloader scope | MECE 原则，属于 content-extractor (Step 03) | — Pending |
| Python CLI 而非 Web App | 下载器是 headless capability，UI 由 content-workbench 提供 | — Pending |
| metadata.json 保留平台原始数据 | 不丢信息，content_item.json 提供统一视图 | — Pending |

---
*Last updated: 2026-03-29 after project initialization*
