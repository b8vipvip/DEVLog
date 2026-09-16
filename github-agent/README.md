# GitHub Agent v4

GitHub Agent v4 是面向高频开发仓库的 GitHub Actions 治理与恢复标准。

核心能力：Fast Gate -> Full Gate、PR-aware concurrency、path-aware heavy builds、Governor `normal cancel -> recheck -> force-cancel`、ghost run 清理/隔离、失败分类、受限 Recovery、AI Repair Brief、Single Release Authority 和 Node24-native action baseline。

- [`GITHUB_AGENT.md`](./GITHUB_AGENT.md)：现行规范。
- [`AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md`](./AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md)：chat2api / GPTWork / fdex / qnbot 审计与整改依据。
- [`AI_REPAIR_HANDOFF.md`](./AI_REPAIR_HANDOFF.md)：Agent → AI 交接规范。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目迁移 SOP。
- [`scripts/`](./scripts/)：Validator / deterministic autofix。
- [`templates/`](./templates/)：Governor、Recovery、Policy Check、CI、Debug、Release、AI discovery 模板。

确定性测试/编译失败不靠 rerun 解决；瞬时 Runner/网络/GitHub 5xx 最多受限重跑一次；普通 ghost 先 normal cancel 再 force-cancel；如果 GitHub 连 force-cancel 都拒绝，则归类为 `GITHUB_PLATFORM_GHOST` 并限流隔离，不进入代码 Recovery，也不计入代码失败率。Release/Deploy/Publish 禁止盲目 replay。
