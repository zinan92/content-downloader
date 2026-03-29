# Requirements: content-downloader

**Defined:** 2026-03-29
**Core Value:** 给一个 URL，拿回标准化的本地文件 — 不管平台，输出格式一致

## v1 Requirements

### Core

- [x] **CORE-01**: CLI 接收单条 URL，自动识别平台（douyin/xhs/wechat-oa/x），路由到对应 adapter
- [x] **CORE-02**: CLI 接收 profile/user URL，批量下载创作者内容
- [x] **CORE-03**: 批量模式支持 `--limit N`（最近 N 条）和 `--since DATE`（增量下载）
- [x] **CORE-04**: 输出目录结构标准化 — `output/{platform}/{author_id}/{content_id}/`
- [x] **CORE-05**: 每个 content_id 目录包含 `media/` + `metadata.json` + `content_item.json`
- [x] **CORE-06**: 全局 `manifest.jsonl` — append-only，一行一个 ContentItem 摘要
- [x] **CORE-07**: ContentItem 数据模型统一 — platform, content_id, content_type, title, description, author_id, author_name, publish_time, source_url, media_files, likes, comments, shares, collects, views

### Adapters

- [x] **ADAPT-01**: 抖音 adapter — 单条视频 URL 下载（去水印 + 封面 + metadata）
- [x] **ADAPT-02**: 抖音 adapter — profile URL 批量下载（支持 post/like/collection 模式）
- [x] **ADAPT-03**: 抖音 adapter — 短链接自动解析（v.douyin.com → 完整 URL）
- [ ] **ADAPT-04**: 小红书 adapter — 单条笔记 URL 下载（图片/视频 + metadata）
- [ ] **ADAPT-05**: 小红书 adapter — profile URL 批量下载
- [ ] **ADAPT-06**: 小红书 adapter — 通过 XHS-Downloader HTTP API 调用（sidecar 模式）
- [ ] **ADAPT-07**: 公众号 adapter — 文章 URL → HTML + 图片 + 音频下载
- [ ] **ADAPT-08**: X adapter — 推文 URL → 图片/视频 + metadata 下载

### Safety

- [x] **SAFE-01**: 所有 adapter 内置请求间隔（可配置，默认 1-3 秒随机）
- [x] **SAFE-02**: 不强制用户登录任何平台（Cookie 可选配置）
- [x] **SAFE-03**: 单条下载失败不影响批量任务其余条目 — 失败记录在 manifest 中
- [x] **SAFE-04**: 去重 — 已下载的 content_id 跳过（可 --force 强制）

### Testing

- [x] **TEST-01**: 每个 adapter 有 fixture 模式 — 离线可测，不需要真实网络
- [ ] **TEST-02**: URL 识别逻辑 100% 覆盖 — 每种 URL 格式有对应测试
- [ ] **TEST-03**: ContentItem 序列化/反序列化测试 — JSON round-trip
- [x] **TEST-04**: manifest.jsonl 并发写入安全

## v2 Requirements

### Extended Platforms

- **EXT-01**: YouTube adapter
- **EXT-02**: Bilibili adapter
- **EXT-03**: Weibo adapter

### Advanced Features

- **ADV-01**: 代理池支持（IP 轮换）
- **ADV-02**: 定时增量下载（cron 模式）
- **ADV-03**: HTTP API 模式（供 content-workbench 调用）
- **ADV-04**: 下载进度 WebSocket 推送

## Out of Scope

| Feature | Reason |
|---------|--------|
| 评论内容抓取 | 额外 API 请求，反爬风险高，属于 signal-scanner |
| 语音转录 (Whisper) | 属于 content-extractor (Step 03) |
| 内容改写/生成 | 属于 content-rewriter (Step 05) |
| 内容发布 | 属于 content-publisher (Step 07) |
| Web UI | 纯 CLI，UI 由 content-workbench 提供 |
| 搜索/关键词发现 | 属于 signal-scanner (Step 01) |
| 数据库持久化 | 用 manifest.jsonl + 文件系统，不引入 DB |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 ~ CORE-07 | Phase 1 | Pending |
| TEST-01 ~ TEST-04 | Phase 1 | Pending |
| SAFE-01 ~ SAFE-04 | Phase 1 | Pending |
| ADAPT-01 ~ ADAPT-03 | Phase 2 | Pending |
| ADAPT-04 ~ ADAPT-06 | Phase 3 | Pending |
| ADAPT-07 | Phase 4 | Pending |
| ADAPT-08 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0

---
*Requirements defined: 2026-03-29*
*Last updated: 2026-03-29 after initial definition*
