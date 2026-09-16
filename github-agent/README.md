# GitHub Agent

`GitHub Agent` 是原 **GitHub Actions 策略** 的正式新名称。当前规范为 **GitHub Agent v4**。

它不是单纯的 YAML 模板，而是一套仓库内自治治理与恢复系统：

1. **Fast Gate / Full Gate**：先运行快速确定性检查，再启动完整测试与重型构建。
2. **Workflow Guard**：PR-aware concurrency、超时、最小权限、发布串行。
3. **Policy Check**：新增/修改 Workflow 时自动检查规则。
4. **Governor v4**：扫描 duplicate / stale / ghost run；普通 cancel 无效时重新检查并 force-cancel。
5. **Failure Taxonomy**：区分 deterministic test、workflow config、infra transient、ghost、superseded、side-effectful。
6. **Recovery**：只对合适的故障取证、确定性修复、Recovery PR 和受限瞬时重跑；ghost run 不进入代码 Recovery。
7. **AI Repair Brief**：需要业务代码推理时，不接 coding-agent provider；把问题整理成标准 Issue，由用户选择的 AI 读取并修复。
8. **Safety Gate**：Release / Deploy / Publish 使用单一 authority，禁止盲目 replay。

## 目录

- [`GITHUB_AGENT.md`](./GITHUB_AGENT.md)：GitHub Agent v4 现行规范。
- [`AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md`](./AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md)：chat2api / GPTWork / fdex / qnbot 高频仓库审计与 v4 设计依据。
- [`AI_REPAIR_HANDOFF.md`](./AI_REPAIR_HANDOFF.md)：Agent → 用户选择 AI 的问题交接格式和修复约束。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目迁移和历史异常恢复 SOP。
- [`scripts/`](./scripts/)：Policy Validator / deterministic autofix。
- [`templates/`](./templates/)：Governor、Recovery、Policy Check、Fast/Full CI、Debug、Release，以及 AI 自动发现入口模板。

## AI 自动发现

部署 GitHub Agent 到新项目时，除 Governor / Recovery / Policy Check 外，默认同时部署：

```text
/AGENTS.md
/.github/GITHUB_AGENT.md
/.github/copilot-instructions.md
```

这样 GitHub Agent 本身仍由 Actions 自动运行，而进入仓库的 AI 能从仓库级指令中得知：先检查 GitHub Agent 规范、未关闭的 `[GitHub Agent][AI Repair]` Issue、关联 Run 日志和 Commit，再进行代码修复。

## v4 默认并发语义

普通 CI 推荐：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

PR 高频更新会淘汰旧 SHA；默认分支已经开始的正式验证允许完成。Release / Deploy / Publish 则串行并使用 `cancel-in-progress: false`。

## 运行原则

Agent 能确定正确修法时自动修复；不能确定时整理事实，不猜业务代码。代码/测试的确定性失败禁止通过重复 rerun 掩盖；只有 Runner/网络/GitHub 5xx 等瞬时故障允许一次受限重跑。

标准交接 Issue 使用：

```text
[GitHub Agent][AI Repair] <workflow> run <run_id>
```

## 兼容说明

为避免破坏已经部署到项目里的 Workflow、检查上下文和历史链接，模板与脚本内部仍可能保留 `actions-*` / `actions_strategy_*` 文件名。它们只是兼容名称，整个系统统一称为 **GitHub Agent**。

现行规范、脚本和模板统一位于仓库根目录的 `github-agent/`。
