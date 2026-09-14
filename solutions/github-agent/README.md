# GitHub Agent

`GitHub Agent` 是原 **GitHub Actions 策略** 的正式新名称。

它不是单纯的 YAML 模板，而是一套仓库内自治治理与恢复系统：

1. **Workflow Guard**：并发、超时、最小权限、发布串行。
2. **Policy Check**：新增/修改 Workflow 时自动检查规则。
3. **Governor**：扫描重复、排队异常、长时间运行和历史卡死任务。
4. **Recovery**：取证、确定性修复、Recovery PR、重新提交和受限瞬时重跑。
5. **AI Repair Brief**：需要业务代码推理时，不接 coding-agent provider；把问题整理成标准 Issue，由用户选择的 AI 读取并修复。
6. **Safety Gate**：禁止自动盲目重放 Release / Deploy / Publish 等有副作用任务。

## 目录

- [`GITHUB_AGENT.md`](./GITHUB_AGENT.md)：GitHub Agent v3 现行规范。
- [`AI_REPAIR_HANDOFF.md`](./AI_REPAIR_HANDOFF.md)：Agent → 用户选择 AI 的问题交接格式和修复约束。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目迁移和历史异常恢复 SOP。
- [`scripts/`](./scripts/)：Policy Validator / deterministic autofix。
- [`templates/`](./templates/)：Governor、Recovery、Policy Check、CI、Debug、Release 模板。

## 运行原则

Agent 能确定正确修法时自动修复；不能确定时就整理事实，不猜业务代码。标准交接 Issue 使用：

```text
[GitHub Agent][AI Repair] <workflow> run <run_id>
```

Issue 会包含 Source Run、Commit、失败 Job/Step、错误摘要、Agent 已执行动作、风险边界和验收标准。用户随后可直接让 AI 读取 Issue、Run 日志和仓库继续开发修复。

## 兼容说明

为避免破坏已经部署到项目里的 Workflow、检查上下文和历史链接，模板与脚本内部仍可能保留 `actions-*` / `actions_strategy_*` 文件名。它们只是兼容名称，整个系统统一称为 **GitHub Agent**。

旧目录 `solutions/github-actions-strategy/` 暂时保留作为历史兼容入口；新的规范入口是本目录 `solutions/github-agent/`。
