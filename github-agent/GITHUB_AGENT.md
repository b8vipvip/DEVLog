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

Release/Deploy/Publish 使用串行 group 和 `cancel-in-progress: false`。

## Node24 baseline

基础 Actions：`actions/checkout@v7`、`actions/setup-python@v7`、`actions/setup-node@v7`、`actions/setup-java@v6`、`actions/upload-artifact@v7`、`actions/download-artifact@v7`。

Android：使用 `android-actions/setup-android@v4`，并显式设置 `packages: platform-tools`；不要沿用默认包含 obsolete `tools` 的 package 列表。平台/build-tools 用后续 `sdkmanager` 显式安装。

GitHub Release：`softprops/action-gh-release@v3` 为 Node24；不要继续使用 Node20 的 v2。

## AI 接手边界

先确认源 SHA 是否已被更新提交取代，读取完整日志，遵守仓库分支/PR 策略，运行原失败测试和相关回归测试，并在 PR 中写清根因、修改、验证和剩余风险。
