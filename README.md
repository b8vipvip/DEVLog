# DEVLog

用于沉淀开发过程中可复用的问题排查、工程规则、自动化策略与解决方案。

## GitHub Agent v4

[`github-agent/`](./github-agent/) 是当前 GitHub Actions 标准：PR-aware concurrency、Fast Gate -> Full Gate、path-aware heavy builds、Governor ghost/platform-ghost handling、失败分类、Single Release Authority、Node24-native action baseline，以及“Agent 自身也遵守目标仓库 PR-only policy”的治理规则。

四个高频项目的审计和整改进度见 [`github-agent/AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md`](./github-agent/AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md)。
