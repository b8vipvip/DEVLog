# GitHub Agent v4

GitHub Agent v4 是面向高频开发仓库的 GitHub Actions 治理与恢复标准。

核心能力：Fast Gate -> Full Gate、PR-aware concurrency、path-aware heavy builds、Governor `normal cancel -> recheck -> force-cancel`、ghost/platform-ghost 隔离、失败分类、受限 Recovery、AI Repair Brief、Single Release Authority 和 Node24-native action baseline。

- [`GITHUB_AGENT.md`](./GITHUB_AGENT.md)：现行规范。
- [`AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md`](./AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md)：chat2api / GPTWork / fdex / qnbot 审计与整改进度。
- [`AI_REPAIR_HANDOFF.md`](./AI_REPAIR_HANDOFF.md)：Agent → AI 交接规范。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目迁移 SOP。
- [`scripts/`](./scripts/)：Validator / deterministic autofix。
- [`templates/`](./templates/)：Governor、Recovery、Policy Check、CI、Debug、Release、AI discovery 模板。

确定性测试/编译失败不靠 rerun；瞬时 Runner/网络/GitHub 5xx 最多受限重跑一次。普通 ghost 先 normal cancel 再 force-cancel；GitHub 连 force-cancel 都拒绝时归类 `GITHUB_PLATFORM_GHOST`，限流隔离且不计入代码失败率。GitHub Agent 自身也必须遵守目标仓库的 PR-only main policy。
