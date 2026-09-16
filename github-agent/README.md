# GitHub Agent

`GitHub Agent` 是原 **GitHub Actions 策略** 的正式新名称。当前规范为 **GitHub Agent v4**。

它不是单纯的 YAML 模板，而是一套仓库内自治治理与恢复系统：Fast Gate / Full Gate、PR-aware concurrency、Policy Check、Governor ghost cleanup、失败分类、受限 Recovery、AI Repair Brief 和 Single Release Authority。

## 目录

- [`GITHUB_AGENT.md`](./GITHUB_AGENT.md)：GitHub Agent v4 现行规范。
- [`AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md`](./AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md)：chat2api / GPTWork / fdex / qnbot 高频仓库审计与整改依据。
- [`AI_REPAIR_HANDOFF.md`](./AI_REPAIR_HANDOFF.md)：Agent → 用户选择 AI 的问题交接格式和修复约束。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目迁移和历史异常恢复 SOP。
- [`scripts/`](./scripts/)：Policy Validator / deterministic autofix。
- [`templates/`](./templates/)：Governor、Recovery、Policy Check、Fast/Full CI、Debug、Release 和 AI 自动发现模板。

## v4 关键行为

- pytest/assertion/compile/lint 等确定性失败不自动 rerun。
- Runner/网络/GitHub 5xx 等瞬时故障最多受限 rerun 一次。
- jobless ghost run：normal cancel -> recheck -> force-cancel，不进入代码 Recovery。
- PR 高频更新淘汰旧 SHA；默认分支已经开始的正式验证通常允许完成。
- 重型构建放在 Fast Gate 之后，并尽量使用 path-aware gate。
- artifact/package build 不等于 Release；每个仓库只有一个最终 Release/Deploy/Publish authority。
- 新模板采用 Node24-native 官方 action major。

## AI 自动发现

部署 GitHub Agent 到新项目时，除 Governor / Recovery / Policy Check 外，默认同时部署：

```text
/AGENTS.md
/.github/GITHUB_AGENT.md
/.github/copilot-instructions.md
```

进入仓库的 AI 应先检查 GitHub Agent 规范、未关闭的 `[GitHub Agent][AI Repair]` Issue、关联 Run 日志和 Commit，再进行代码修复。

## 兼容说明

模板与脚本内部继续保留 `actions-*` / `actions_strategy_*` 文件名以兼容已部署仓库。它们只是内部实现名称，整个系统统一称为 **GitHub Agent v4**。
