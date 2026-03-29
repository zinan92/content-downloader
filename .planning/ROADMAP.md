# Roadmap: content-downloader

**Created:** 2026-03-29
**Milestone:** v1.0 — 4 平台统一下载

## Phase Overview

| Phase | Name | Requirements | Goal |
|-------|------|-------------|------|
| 1 | 1/1 | Complete   | 2026-03-29 |
| 2 | 1/1 | Complete   | 2026-03-29 |
| 3 | XHS Adapter | ADAPT-04~06 | XHS-Downloader HTTP API 集成，小红书下载可用 |
| 4 | WeChat OA Adapter | ADAPT-07 | 公众号文章 HTML + 图片下载可用 |
| 5 | X Adapter | ADAPT-08 | X/Twitter 媒体下载可用 |

---

## Phase 1: Scaffold + Core

**Goal:** CLI 骨架 + adapter 接口 + ContentItem 模型 + manifest + fixture adapter 完整跑通

**Requirements:** CORE-01~07, TEST-01~04, SAFE-01~04

**Success Criteria:**
- `python -m content_downloader download <fixture-url>` 产出标准目录结构
- `python -m content_downloader download <fixture-profile-url> --limit 3` 批量下载 3 条
- manifest.jsonl 正确追加
- ContentItem JSON schema 验证通过
- fixture adapter 全绿

**Key Deliverables:**
- `content_downloader/models.py` — ContentItem, DownloadResult, DownloadError dataclasses
- `content_downloader/adapters/base.py` — PlatformAdapter protocol
- `content_downloader/adapters/fixture.py` — Fixture adapter for testing
- `content_downloader/router.py` — URL → platform 识别 + adapter 路由
- `content_downloader/manifest.py` — JSONL manifest 读写
- `content_downloader/cli.py` — CLI entry point (click/typer)
- `tests/` — 全覆盖

---

## Phase 2: Douyin Adapter

**Goal:** 移植 douyin-downloader-1 核心能力，真实抖音视频下载可用

**Requirements:** ADAPT-01~03

**Success Criteria:**
- `python -m content_downloader download "https://www.douyin.com/video/xxx"` 下载去水印视频 + metadata
- `python -m content_downloader download "https://www.douyin.com/user/xxx" --limit 5` 批量下载
- `https://v.douyin.com/xxx` 短链接自动解析
- 输出 ContentItem 格式与 fixture adapter 一致

**Key Deliverables:**
- `content_downloader/adapters/douyin/` — adapter 实现
- 从 douyin-downloader-1 移植: URL 解析、API client、签名、下载逻辑
- 砍掉: 转录、归档、分析（不在 scope）

---

## Phase 3: XHS Adapter

**Goal:** XHS-Downloader HTTP API 集成，小红书笔记下载可用

**Requirements:** ADAPT-04~06

**Success Criteria:**
- `python -m content_downloader download "https://www.xiaohongshu.com/explore/xxx"` 下载图片/视频
- `python -m content_downloader download "https://www.xiaohongshu.com/user/profile/xxx" --limit 10` 批量
- XHS-Downloader 作为 sidecar 自动启动/检测
- 输出 ContentItem 格式一致

**Key Deliverables:**
- `content_downloader/adapters/xhs/` — HTTP API client wrapper
- XHS-Downloader sidecar 管理（启动检测、健康检查）
- XHS metadata → ContentItem 映射

---

## Phase 4: WeChat OA Adapter

**Goal:** 公众号文章下载可用

**Requirements:** ADAPT-07

**Success Criteria:**
- `python -m content_downloader download "https://mp.weixin.qq.com/s/xxx"` 下载文章 HTML + 图片 + 音频
- metadata 包含标题、作者、发布时间、阅读数（如有）
- 输出 ContentItem 格式一致

**Key Deliverables:**
- `content_downloader/adapters/wechat_oa/` — HTTP 抓取 + 图片提取

---

## Phase 5: X Adapter

**Goal:** X/Twitter 媒体下载可用

**Requirements:** ADAPT-08

**Success Criteria:**
- `python -m content_downloader download "https://x.com/user/status/xxx"` 下载图片/视频
- metadata 包含推文文本、engagement metrics
- 输出 ContentItem 格式一致

**Key Deliverables:**
- `content_downloader/adapters/x/` — yt-dlp 封装或 API client

---

## Dependencies

```
Phase 1 (Scaffold) ── 无依赖
Phase 2 (Douyin)   ── depends on Phase 1
Phase 3 (XHS)      ── depends on Phase 1
Phase 4 (WeChat)   ── depends on Phase 1
Phase 5 (X)        ── depends on Phase 1

Phase 2~5 之间互相独立，可并行
```

---
*Roadmap created: 2026-03-29*
*Last updated: 2026-03-29 after initial definition*
