# GitHub Agent v3

GitHub Agent v3 是原“GitHub Actions 策略 v3”的正式新名称。它以 GitHub Actions 作为执行底座，在仓库内提供 **预防、检查、运行时治理、历史异常恢复、确定性自动修复和 AI Repair Brief 交接**。

GitHub Agent **不接入、不调用 coding-agent provider**。当问题需要理解业务代码时，Agent 只负责把问题整理完整，由用户随后让自己选择的 AI 读取并修复。

## 1. GitHub 原生提供什么

GitHub Actions 原生能够读取 Workflow/Job 状态与日志、Cancel、Re-run、workflow_dispatch，并在权限允许时写分支、提交、PR、Issue。这些属于运行与控制能力，不等于理解代码并自动修复。

## 2. GitHub Agent 的修复分层

### L0：运行控制

发现 duplicate / stale run 后先释放 Runner：Cancel、去重、超时保护。

### L1：确定性 Workflow 修复

`actions_strategy_autofix.py` 负责可以机械判断的缺陷，例如缺少 `workflow_dispatch`、最小 `permissions`、`concurrency`、`cancel-in-progress`、发布串行保护和 Job `timeout-minutes`。

### L2：项目确定性代码修复

项目可提供 `.github/actions-recovery.sh`。只有某个业务/测试故障已经形成明确、幂等修复规则时，Agent 才自动修改源代码、测试或配置，然后提交 Recovery PR。

### L3：AI Repair Brief

如果问题需要业务理解、跨文件推理或新的代码修法，Agent 不猜、不调用外部 coding agent，而是创建：

`[GitHub Agent][AI Repair] <workflow> run <run_id>`

标准 Issue 至少包含：

- Source Run / Workflow / Workflow path；
- branch / commit SHA / event / attempt；
- Governor / Recovery reason；
- failed jobs / steps；
- 高信号错误行摘要；
- 是否检测到瞬时基础设施故障；
- 是否属于 Release / Deploy 等有副作用任务；
- 自动修复 PR（如有）；
- Agent 已执行的 Cancel / repair / rerun 动作；
- 给接手 AI 的任务、约束和验收标准。

用户随后让 AI 读取该 Issue、完整 Run 日志、对应 Commit 和仓库代码即可继续修复。

详见 [`AI_REPAIR_HANDOFF.md`](./AI_REPAIR_HANDOFF.md)。

## 3. 标准恢复链路

```text
失败 / 卡死 / 历史异常 run
          ↓
Governor 判定 duplicate / stale
          ↓
Cancel 释放 Runner
          ↓
Recovery 收集 metadata + jobs + logs
          ↓
L1 Workflow 确定性修复？
   ├─ 是 → Recovery PR → 验证
   └─ 否
          ↓
L2 项目已知规则可修？
   ├─ 是 → 修改代码/测试 → Recovery PR → CI
   └─ 否
          ↓
生成 AI Repair Brief Issue
          ↓
用户让 AI 读取 Issue / Run / 代码
          ↓
AI 创建修复分支 + PR + CI
```

## 4. 瞬时故障

只有日志明显匹配 Runner、网络、DNS、502/503/504、连接重置等瞬时故障时，Agent 才允许一次受限 fresh rerun。无论是否 rerun，只要没有确定性修复，问题仍必须生成 AI Repair Brief，防止故障被重跑掩盖。

## 5. AI 接手后的强制边界

接手 AI 应：

- 先确认源 Commit 是否已被更新提交取代；
- 阅读完整日志，不只依赖摘要；
- 使用独立修复分支，默认禁止直接写 `main`；
- 运行原失败测试、相关回归测试、Policy Check；
- PR 中写清根因、修改、验证、剩余风险；
- Release / Deploy / Publish / Store Package 禁止盲目重放。

## 6. 重新运行不等于修复

Re-run 仍然执行原始代码。如果根因在代码里，单纯重跑只会重复错误。因此 GitHub Agent 只把 rerun 用作受限的瞬时环境恢复；代码问题必须产生新 Commit 后再验证。

## 7. 版本与兼容

- 对外名称：**GitHub Agent v3**。
- 旧名称：GitHub Actions 策略 v3（历史称呼）。
- `actions-*` / `actions_strategy_*` 文件名继续作为内部兼容实现名称。
- 新项目文档统一使用 `GITHUB_AGENT.md`。
