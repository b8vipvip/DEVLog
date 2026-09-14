# GitHub Agent v3

GitHub Agent v3 是原“GitHub Actions 策略 v3”的正式新名称。它以 GitHub Actions 作为执行底座，在仓库内提供 **预防、检查、运行时治理、历史异常恢复、确定性自动修复和可选 AI 代码修复委派**。

## 1. GitHub 原生提供什么

GitHub Actions 原生能够：

- 读取 Workflow / Job 状态与日志；
- Cancel 运行；
- Re-run 整个 Workflow、失败 Job 或指定 Job；
- 通过 `workflow_dispatch` 重新触发工作流；
- 使用仓库权限写分支、提交、PR、Issue（取决于 token 权限）。

这些能力属于“执行与控制”，不等于“理解代码并自动修复”。GitHub Actions 本身不会凭日志自动推断任意业务代码应该怎么改。

GitHub 另有 Copilot cloud agent、GitHub Agentic Workflows 等 coding-agent 能力，可以分析失败、修改代码并提交分支/PR。GitHub Agent 可以把这类 coding agent 作为可选的智能修复 provider，但它们不是 Actions 自带的通用自动修复器。

## 2. GitHub Agent 的修复分层

### L0：运行控制

发现重复或 stale run 后先释放 Runner：Cancel / 去重 / 超时保护。

### L1：确定性 Workflow 修复

`actions_strategy_autofix.py` 负责可以机械判断的缺陷，例如：

- 缺少 `workflow_dispatch`；
- 缺少最小 `permissions`；
- 缺少 `concurrency`；
- 普通任务缺少 `cancel-in-progress: true`；
- 发布类任务缺少串行保护；
- `runs-on` Job 缺少 `timeout-minutes`。

这类修复无需 AI，可以自动创建 recovery branch / PR，并重新提交普通 Workflow 验证。

### L2：项目确定性代码修复

项目可提供 `.github/actions-recovery.sh`。当某个业务/测试故障已经建立明确、幂等的修复规则时，GitHub Agent 可根据 `ACTIONS_RECOVERY_LOG` 自动修改源代码、测试或配置，然后提交 Recovery PR。

典型适用：

- 某 fixture 必须补固定 metadata；
- 某测试需要固定 timeout；
- 某生成文件需要重新同步；
- 某已知版本兼容问题需要固定替换。

### L3：AI 代码修复

如果问题需要理解业务逻辑、跨文件推理或根据日志设计新修法，确定性脚本不应该猜测。此时可以委派 coding-agent provider，例如：

- GitHub Copilot cloud agent；
- GitHub Agentic Workflows 支持的 Copilot CLI / Codex / Claude Code / Gemini CLI 等 coding agent。

AI 修复必须遵守安全边界：

- 只允许写 recovery/PR 分支，默认禁止直接写 `main`；
- 必须重新执行原失败测试和 Policy Check；
- 限制自动迭代次数；
- Release / Deploy / Publish 等有外部副作用的任务不得自动盲目重放；
- 失败或低置信度时升级为 Recovery Incident，保留人工审查点。

## 3. 标准恢复链路

```text
失败 / 卡死 / 历史异常 run
          ↓
Governor 取状态并判定 duplicate / stale
          ↓
释放 Runner（Cancel）
          ↓
Recovery 收集 metadata + logs
          ↓
L1 Workflow 确定性修复？
   ├─ 是 → 修改 → recovery branch/PR → 重新 dispatch
   └─ 否
          ↓
L2 项目已知修复规则？
   ├─ 是 → 修改代码/测试 → PR → CI
   └─ 否
          ↓
L3 coding-agent provider 已启用？
   ├─ 是 → AI 分析并改代码 → PR → CI → 限次迭代
   └─ 否 → bounded rerun / Recovery Incident
```

## 4. 为什么先 Cancel 再修

历史卡死任务已经占用 Runner。继续让它运行不会让修复代码“注入”到已启动的进程里，因此必须先释放资源，再基于原 run 的 SHA、分支、Workflow、日志创建新的修复提交和验证运行。

## 5. 重新运行不等于修复

GitHub 原生 Re-run 使用原始 `GITHUB_SHA` / `GITHUB_REF`。如果根因在代码里，单纯 rerun 只会重复执行原代码；因此 GitHub Agent 只有在判断为 Runner、网络或临时环境故障时才使用 bounded fresh rerun。代码缺陷应先生成新提交，再运行新的验证。

## 6. 版本与兼容

- 对外名称：**GitHub Agent v3**。
- 旧名称：GitHub Actions 策略 v3（历史称呼）。
- `actions-*` / `actions_strategy_*` 文件名可暂时保留作为兼容实现名称，避免破坏历史工作流、已有引用或 required-check 上下文。
- 新项目文档统一使用 `GITHUB_AGENT.md`。
