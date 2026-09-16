# GitHub Agent v4

GitHub Agent v4 是面向高频开发仓库的 GitHub Actions 治理标准。

## 原则

- 确定性 pytest/assertion/compile/lint/contract failure 必须由新 commit 修复，不自动 rerun。
- Runner/网络/GitHub 5xx 等瞬时故障最多受限 rerun 一次。
- 长期 queued/in_progress 且无 job、或普通 cancel 无效的 run 属于 `GHOST_RUN`：normal cancel -> recheck -> force-cancel，不进入代码 Recovery。
- PR 只保留最新 SHA；默认分支已经运行的正式验证允许完成。
- Fast Gate 先于 Full Gate；重型任务按改动路径选择执行。
- 每个仓库只有一个最终 Release/Deploy/Publish authority；artifact/package build 不等于发布。

## 失败分类

`DETERMINISTIC_TEST`、`WORKFLOW_CONFIG`、`INFRA_TRANSIENT`、`GHOST_RUN`、`SUPERSEDED`、`SIDE_EFFECTFUL`。

## Governor v4

L0 Governor 清理 duplicate/stale/ghost run。普通 cancel 后重新读取状态；仍 queued/in_progress 才调用 force-cancel。queued 且无 job 的 run 不触发 Recovery。PR/feature branch 旧 SHA 可以淘汰，默认分支已经 in-progress 的普通验证不因 duplicate 规则被强杀。

## Recovery

L1 `actions_strategy_autofix.py` 只修机械可判断的 workflow 缺陷。L2 项目可提供 `.github/actions-recovery.sh` 执行已知、幂等的确定性修复。L3 无法机械修复时创建 `[GitHub Agent][AI Repair] <workflow> run <run_id>`，交给用户选择的 AI。

Recovery 先分类；只有明显的瞬时基础设施故障且没有确定性失败信号时才允许一次 fresh rerun。Release/Deploy/Publish 不盲目 replay。

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

`actions/checkout@v7`、`actions/setup-python@v7`、`actions/setup-node@v7`、`actions/setup-java@v6`、`actions/upload-artifact@v7`、`actions/download-artifact@v7`。

## AI 接手边界

先确认源 SHA 是否已被更新提交取代，读取完整日志，使用独立修复分支，运行原失败测试和相关回归测试，并在 PR 中写清根因、修改、验证和剩余风险。
