# GitHub Agent v4

GitHub Agent v4 是面向高频开发仓库的 GitHub Actions 治理标准。

## 原则

- 确定性 pytest/assertion/compile/lint/contract failure 必须由新 commit 修复，不自动 rerun。
- Runner/网络/GitHub 5xx 等瞬时故障最多受限 rerun 一次。
- 长期 queued/in_progress 且无 job、或普通 cancel 无效的 run 属于 `GHOST_RUN`：normal cancel -> recheck -> force-cancel，不进入代码 Recovery。
- 如果 GitHub 连 force-cancel 都拒绝且 run 仍 active，则升级为 `GITHUB_PLATFORM_GHOST`：限流隔离、保留证据，不反复消耗 Runner，也不计入代码失败率。
- PR 只保留最新 SHA；默认分支已经运行的正式验证允许完成。
- Fast Gate 先于 Full Gate；重型任务按改动路径选择执行。
- 每个仓库只有一个最终 Release/Deploy/Publish authority；artifact/package build 不等于发布。
- **尊重仓库自身的 PR-only main policy**：GitHub Agent 的治理/修复提交也必须走分支 + PR，不能为了修 CI 绕过仓库治理。
- **Workflow 也是 contract**：如果 tests 会读取 `.github/workflows/*.yml`，修改 CI 拓扑时必须在同一 PR 更新这些 contract tests；这类 assertion failure 属于确定性代码/测试问题，不属于 Runner 故障。

## 失败分类

`DETERMINISTIC_TEST`、`WORKFLOW_CONFIG`、`INFRA_TRANSIENT`、`GHOST_RUN`、`GITHUB_PLATFORM_GHOST`、`SUPERSEDED`、`SIDE_EFFECTFUL`。

## Governor v4

普通 cancel 后重新读取状态；仍 queued/in_progress 才调用 force-cancel。queued 且无 job 的 run 不触发 Recovery。force-cancel 仍被 GitHub 拒绝时标记平台 ghost，并限制每轮尝试数量。PR/feature branch 旧 SHA 可以淘汰，默认分支已经 in-progress 的普通验证不因 duplicate 规则被强杀。

Governor 是兜底治理，不应该自己制造大量 Actions。标准模板使用每小时一次、错开整点的 `17 * * * *`；不要默认使用 `*/10 * * * *`。后者每个仓库每天会额外创建 144 次 Governor run，而 hourly 只创建 24 次。高频提交的热路径去重交给 workflow 自身的 concurrency，Governor 主要负责 stale/ghost cleanup。

## Recovery

`actions_strategy_autofix.py` 只修机械可判断的 workflow 缺陷；项目可提供 `.github/actions-recovery.sh` 执行已知、幂等的确定性修复；无法机械修复时创建 `[GitHub Agent][AI Repair] <workflow> run <run_id>`。只有明显的瞬时基础设施故障且没有确定性失败信号时才允许一次 fresh rerun。Release/Deploy/Publish 不盲目 replay。

## CI 拓扑

```text
push / pull_request
        ↓
Fast Gate: syntax / lint / compile / focused contracts
        ↓ success
Full Gate: pytest / Docker / Android / Windows / package
        ↓ success
Release Gate（需要时）
        ↓
Release / Deploy / Publish
```

普通 CI 推荐：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

同时监听 `push` 和 `pull_request` 的普通 workflow 不允许继续使用字面量 `cancel-in-progress: true`：那会让默认分支正在执行的正式验证被后续 push 中断。也不应使用字面量 `false`：那会让同一 PR 的旧 SHA 持续浪费 Runner。Policy Check/Autofix 应把这类旧配置迁移为 PR-aware expression。

Release/Deploy/Publish 使用串行 group 和 `cancel-in-progress: false`。

## workflow_run 与发布降噪

`workflow_run` 的分支限制应尽量放在触发器本身，例如：

```yaml
on:
  workflow_run:
    workflows: ["Build and Test"]
    types: [completed]
    branches: [main]
```

不要只在 job `if:` 中判断 `head_branch == main`。后者仍会为每个 PR 完成事件创建一个最终 `skipped` 的 workflow run，继续污染 Actions 列表和运行统计。

如果重型 build 的 `paths` 包含 workflow 文件本身，那么纯 CI 改动也可能成功触发 build。下游自动 Release 不能把“build 成功”直接等同于“产品需要发布”；应增加 release eligibility gate，确认 source commit/range 实际修改了产品路径后才创建版本。`workflow_dispatch` 可以保留为人工显式发布入口。

最终 Release authority 应直接上传稳定版本所需的全部标准资产。不要为了给同一个 Release 再挂一个固定 rescue/manifest/helper 资产，就在 Publish 完成后链式启动第二条 workflow；这会让 skipped/no-op publish 也产生连锁 run。独立资产 workflow 更适合“该资产自身发生变化时，回写当前最新稳定版本”的场景。

### 多工作流 Release Gate：事件驱动，不占 Runner 轮询

当 Release 必须同时等待多个默认分支验证（例如 `CI` + `Production image smoke`）时，不允许先启动 Release job，再用 `sleep` / API polling 占住 Runner 等其它 workflow 完成。标准做法是让 Release 同时监听这些验证的 `workflow_run: completed` 事件，并对触发 SHA 做一次快照检查：

1. 第一个验证完成时，如果同 SHA 的其它必需验证尚未完成，Release 快速成功退出，不 checkout、不发布、不等待。
2. 后续验证完成会再次触发 Release；只有同一 SHA 的全部必需验证都 `completed + success` 时才取得发布权。
3. Release 使用固定串行 concurrency group + `cancel-in-progress: false`，并在创建 Release 前检查目标版本是否已存在，因此多个 completion 事件不会重复发布。
4. 查询必须绑定精确 `head_sha`，并只接受默认分支的正式 `push` 验证；不要把 PR 验证或其它 SHA 的成功结果拼进发布条件。
5. `workflow_dispatch` 可以保留，但手工指定的 source SHA 也必须通过同一组正式验证，不得绕过 Release Gate。

这种模式把“最多等待 N 分钟”的 Runner polling 改成几个秒级事件处理：peer 未完成时立即 no-op，最终 peer 完成时执行真实 Release。chat2api 已在真实 main 合并链路验证该模式：第一次 Release 在 peer pending 时快速退出，第二次在 `CI` 与 `Production image smoke` 均成功后取得发布权。

## Node24 baseline

基础 Actions：`actions/checkout@v7`、`actions/setup-python@v7`、`actions/setup-node@v7`、`actions/setup-java@v6`、`actions/upload-artifact@v7`、`actions/download-artifact@v7`。

Android：使用 `android-actions/setup-android@v4`，并显式设置 `packages: platform-tools`；不要沿用默认包含 obsolete `tools` 的 package 列表。平台/build-tools 用后续 `sdkmanager` 显式安装。

GitHub Release：`softprops/action-gh-release@v3` 为 Node24；不要继续使用 Node20 的 v2。

## AI 接手边界

先确认源 SHA 是否已被更新提交取代，读取完整日志，遵守仓库分支/PR 策略，运行原失败测试和相关回归测试，并在 PR 中写清根因、修改、验证和剩余风险。
