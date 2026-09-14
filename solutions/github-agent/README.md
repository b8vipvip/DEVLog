# GitHub Agent

`GitHub Agent` 是原 **GitHub Actions 策略** 的正式新名称。

它不是单纯的 YAML 模板，而是一套仓库内自治治理与恢复系统：

1. **Workflow Guard**：并发、超时、最小权限、发布串行。
2. **Policy Check**：新增/修改 Workflow 时自动检查规则。
3. **Governor**：扫描重复、排队异常、长时间运行和历史卡死任务。
4. **Recovery**：取证、确定性修复、Recovery PR、重新提交和限次重跑。
5. **Code Repair Adapter**：已知故障可用项目 hook 自动修；任意业务代码需要接 coding-agent provider。
6. **Safety Gate**：禁止自动盲目重放 Release / Deploy / Publish 等有副作用任务。

## 目录

- [`GITHUB_AGENT.md`](./GITHUB_AGENT.md)：GitHub Agent v3 规范与修复能力边界。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目迁移和历史异常恢复 SOP。
- [`scripts/`](./scripts/)：Policy Validator / deterministic autofix。
- [`templates/`](./templates/)：Governor、Recovery、Policy Check、CI、Debug、Release 模板。

## 兼容说明

为避免破坏已经部署到项目里的 Workflow、检查上下文和历史链接，模板与脚本内部仍可能保留 `actions-*` / `actions_strategy_*` 文件名。它们只是兼容名称，整个系统从现在起统一称为 **GitHub Agent**。

旧目录 `solutions/github-actions-strategy/` 暂时保留作为历史兼容入口；新的规范入口是本目录 `solutions/github-agent/`。
