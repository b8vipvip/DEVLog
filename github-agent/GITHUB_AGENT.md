# GitHub Agent v4

GitHub Agent v4 是面向高频开发仓库的 GitHub Actions 治理标准。它以 GitHub Actions 作为执行底座，在仓库内提供 **预防、Fast Gate、运行时治理、ghost run 清理、失败分类、确定性自动修复和 AI Repair Brief 交接**。

GitHub Agent **不接入、不调用 coding-agent provider**。当问题需要理解业务代码时，Agent 负责把证据整理完整，由用户选择的 AI 读取并修复。

## 核心原则

- **代码失败不重跑**：pytest assertion、compile、lint、contract failure 必须由新 commit 修复。
- **瞬时基础设施故障最多重跑一次**：Runner lost、DNS、connection reset、502/503/504 等才允许 fresh rerun。
- **ghost run 不是代码失败**：长期 queued/in_progress 且没有 job，或普通 cancel 无效时，进入 force-cancel 清理链路，不生成代码 Recovery。
- **PR 与默认分支采用不同并发策略**：PR 只保留最新 SHA；默认分支已经运行的正式验证允许完成。
- **Fast Gate 先于 Full Gate**：语法、lint、compile、关键 contract 先通过，再启动完整 pytest、Docker、Windows installer、Android 等重任务。
- **Path-aware CI**：只运行与本次改动范围有关的重任务。
- **Single Release Authority**：每个仓库只有一个 workflow 拥有最终 Release/Deploy/Publish 权限；artifact/package build 不等同于发布。

## 失败分类

- `DETERMINISTIC_TEST`：测试、断言、编译、lint、静态契约失败。禁止自动 rerun。
- `WORKFLOW_CONFIG`：YAML、action、permissions、workflow 配置错误。修 workflow 后以新 commit 验证。
- `INFRA_TRANSIENT`：Runner/网络/GitHub 5xx 等瞬时故障。最多一次受限 rerun。
- `GHOST_RUN`：长期 active、无 job、普通 cancel 无效。normal cancel -> recheck -> force-cancel，不进入代码 Recovery。
- `SUPERSEDED`：旧 PR/feature SHA 已被新 SHA 取代。直接取消。
- `SIDE_EFFECTFUL`：Release/Deploy/Publish。串行执行，禁止盲目 replay。

## 修复分层

### L0：运行控制

Governor 负责 duplicate、stale、ghost run：普通 cancel；重新读取 run 状态；若仍 queued/in_progress，则调用 force-cancel；queued 且无 job 的 run 标记为 `GHOST_RUN`，不触发 Recovery。

### L1：确定性 Workflow 修复

`actions_strategy_autofix.py` 负责机械可判断的缺陷：`workflow_dispatch`、最小 `permissions`、`concurrency`、Job `timeout-minutes` 等。v4 不再把 `Store Package` / artifact build 按名称自动视为生产副作用 workflow；只有 Release / Deploy / Publish 属于默认 side-effectful 类别。

### L2：项目确定性代码修复

项目可提供 `.github/actions-recovery.sh`。只有某个业务/测试故障已经形成明确、幂等修复规则时，Agent 才自动修改源代码、测试或配置，然后提交 Recovery PR。

### L3：AI Repair Brief

如果问题需要业务理解、跨文件推理或新的代码修法，Agent 创建 `[GitHub Agent][AI Repair] <workflow> run <run_id>`。Issue 应包含 Source Run、workflow/path、branch/SHA/event/attempt、失败 jobs/steps、高信号日志、失败分类、是否有副作用、Agent 已采取的动作以及验收标准。

## 标准 CI 拓扑

```text
push / pull_request
        ↓
     Fast Gate
 syntax / lint / compile
 focused contract tests
        ↓ success
     Full Gate
 pytest / Docker / Android
 Windows build / package
        ↓ success
 release gate (仅需要时)
        ↓
 Release / Deploy / Publish
```

重型任务应通过 `needs:`、changed-path detection 或独立 workflow gate 延后启动。不要让一个已知会失败的 Fast Gate 同时启动多个昂贵构建。

## Concurrency v4

普通 CI 推荐：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

高频 PR 只保留最新 SHA；默认分支 push 已经开始的正式验证不会被后续 push 强杀。

Release / Deploy / Publish：

```yaml
concurrency:
  group: production-release
  cancel-in-progress: false
```

Governor 同样遵守该边界：默认分支正在运行的普通验证不因 duplicate 规则被取消；旧 queued run 仍可清理。

## Node24 Actions 基线

2026-09 起新模板使用 Node24-native 官方 action major：

- `actions/checkout@v7`
- `actions/setup-python@v7`
- `actions/setup-node@v7`
- `actions/setup-java@v6`
- `actions/upload-artifact@v7`
- `actions/download-artifact@v7`

第三方 action 升级前必须确认其 Node24 兼容性。

## 重新运行不等于修复

Re-run 仍执行原始代码。确定性失败继续重跑只会制造重复红灯并消耗 Runner。v4 的 Recovery 必须先分类，再决定 rerun、force-cancel、创建修复 PR 或生成 AI Repair Brief。

## AI 接手边界

接手 AI 应先确认源 SHA 是否已被更新提交取代，读取完整日志，使用独立修复分支，运行原失败测试和相关回归测试，并在 PR 中写清根因、修改、验证和剩余风险。Release / Deploy / Publish 禁止盲目重放。

## 版本与兼容

- 对外名称：**GitHub Agent v4**。
- v3 文档和文件名继续作为历史兼容。
- `actions-*` / `actions_strategy_*` 文件名继续作为内部实现名称。
- 新项目统一从 `templates/` 复制 v4 基线，再按项目拆 Fast/Full/Path Gate。
