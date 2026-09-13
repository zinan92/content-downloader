# AGENTS.md — content-downloader

## Operating pointer

Read `docs/agents/domain.md` and the relevant repository docs before changing
an adapter. The project-specific issue tracker is described in
`docs/agents/issue-tracker.md`; the canonical company rules remain in Park OS.

## Project delta

- **Repository purpose:** 将抖音、小红书、公众号和 X 内容下载到统一的本地文件结构，供下游内容工具复用。
- **Local non-negotiables:** `content-downloader` is the only Douyin download entry for content-studio; keep the existing adapter and output contract; authentication cookies stay outside Git.
- **Verify with:** `python3 -m pytest -q`; `git diff --check`; `gitleaks detect --source . --no-banner`（若已安装）。
- **Do not:** 不代用户登录或操作账号；不提交 cookies、真实下载产物或凭据；不增加第二条抖音下载链路；遇到验证码或风控立即停止。

## Agent skills

### Issue tracker

Issues for this repo live on GitHub at `zinan92/content-downloader`; use the
`gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the canonical five labels mapped in `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository. See `docs/agents/domain.md` for the
consumer rules.
