# GitHub Agent

`GitHub Agent` 是原 **GitHub Actions 策略** 的正式新名称。

它不是单纯的 YAML 模板，而是一套仓库内自治治理与恢复系统：

1. **Workflow Guard**：并发、超时、最小权限、发布串行。
2. **Policy Check**：新增/修改 Workflow 时自动检查规则。
3. **Governor**：扫描重复、排队异常、长时间运行和历史卡死任务。
4. **Recovery**：取证、确定性修复、Recovery PR、重新提交和受限瞬时重跑。
5. **AI Repair Brief**：需要业务代码推理时，不接 coding-agent provider；把问题整理成标准 Issue，由用户选择的 AI 读取并修复。
6. **AI Discovery**：根目录 `AGENTS.md` 作为通用 AI 入口，`.github/copilot-instructions.md` 作为 GitHub Copilot 入口，让 AI 在进入项目时自动发现 GitHub Agent 的交接规则。
7. **Safety Gate**：禁止自动盲目重放 Release / Deploy / Publish 等有副作用任务。

## 目录

- [`GITHUB_AGENT.md`](./GITHUB_AGENT.md)：GitHub Agent v3 现行规范。
- [`AI_REPAIR_HANDOFF.md`](./AI_REPAIR_HANDOFF.md)：Agent → 用户选择 AI 的问题交接格式和修复约束。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目迁移和历史异常恢复 SOP。
- [`scripts/`](./scripts/)：Policy Validator / deterministic autofix。
- [`templates/`](./templates/)：Governor、Recovery、Policy Check、CI、Debug、Release，以及 AI 自动发现入口模板。
- [`templates/AGENTS.md`](./templates/AGENTS.md)：部署到目标仓库根目录 `/AGENTS.md`。
- [`templates/copilot-instructions.md`](./templates/copilot-instructions.md)：部署到目标仓库 `/.github/copilot-instructions.md`。

## AI 自动发现

部署 GitHub Agent 到新项目时，除 Governor / Recovery / Policy Check 外，默认同时部署：

```text
/AGENTS.md
/.github/GITHUB_AGENT.md
/.github/copilot-instructions.md
```

这样 GitHub Agent 本身仍由 Actions 自动运行，而进入仓库的 AI 能从仓库级指令中得知：先检查 GitHub Agent 规范、未关闭的 `[GitHub Agent][AI Repair]` Issue、关联 Run 日志和 Commit，再进行代码修复。

`AGENTS.md` 是通用 AI 入口；`.github/copilot-instructions.md` 是 GitHub Copilot 的专用补充入口。AI 是否原生支持仓库指令文件由具体产品决定，因此不能假设所有 AI 都会无条件读取，但支持这些约定的 AI 无需用户每次重复声明 GitHub Agent 的存在。

## 运行原则

Agent 能确定正确修法时自动修复；不能确定时就整理事实，不猜业务代码。标准交接 Issue 使用：

```text
[GitHub Agent][AI Repair] <workflow> run <run_id>
```

Issue 会包含 Source Run、Commit、失败 Job/Step、错误摘要、Agent 已执行动作、风险边界和验收标准。用户随后可直接让 AI 读取 Issue、Run 日志和仓库继续开发修复。

## 兼容说明

为避免破坏已经部署到项目里的 Workflow、检查上下文和历史链接，模板与脚本内部仍可能保留 `actions-*` / `actions_strategy_*` 文件名。它们只是兼容名称，整个系统统一称为 **GitHub Agent**。

旧目录 `solutions/github-actions-strategy/` 暂时保留作为历史兼容入口；新的规范入口是本目录 `solutions/github-agent/`。
