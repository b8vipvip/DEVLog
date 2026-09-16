# GitHub Actions 高频仓库深度审计（2026-09-16）

审计对象：`b8vipvip/chat2api`、`b8vipvip/GPTWork`、`b8vipvip/fdex`、`b8vipvip/qnbot`。

状态：**整改实施中**。GitHub Agent v4 标准已完成第一阶段：Governor force-cancel ghost run、PR-aware concurrency、失败分类、Fast/Full CI 模板、Node24-native action baseline。项目落地顺序为 `GPTWork -> qnbot -> chat2api -> fdex`。

## 审计结论

近期红灯由三类问题叠加：确定性代码/测试失败、Workflow 拓扑放大、GitHub 平台 ghost run 残留。v4 因此不再采用“失败就 rerun”的简单策略。

### chat2api

基础治理较完整。主要问题已经转为架构迁移时 contract tests 未同步、production smoke 硬编码契约、release workflow 占 Runner 轮询前置检查，以及历史 queued ghost run。

### GPTWork

优先级最高。存在多批长期 queued 且无 job 的 ghost run，v3 Governor 普通 cancel 无法清理；Store Package 在 PR 阶段过早启动完整 Windows/Linux 打包，并被 v3 错当成 release 类副作用 workflow；多个辅助 workflow 缺 timeout/concurrency。

### fdex

代表性失败为 FastAPI/UI contract 与新实现不同步。feature/fix/agent push + pull_request 可能产生双触发；FastAPI 与 Android build 缺 path-aware gate；发布职责需要收敛。

### qnbot

同一提交会在 API CI 与 Windows build 中重复执行 repository static tests，一个 assertion failure 被放大成多条红灯。API-only 改动也可能启动完整 Windows 构建；多个 workflow 缺 concurrency/timeout；旧 action major 需要迁移 Node24-native 版本。

## GitHub Agent v4 标准

- `DETERMINISTIC_TEST`：pytest/assertion/compile/lint，禁止自动 rerun。
- `WORKFLOW_CONFIG`：修 workflow 后以新 commit 验证。
- `INFRA_TRANSIENT`：Runner/网络/GitHub 5xx，最多一次受限 rerun。
- `GHOST_RUN`：长期 active、无 job 或 normal cancel 无效，进入 force-cancel。
- `SUPERSEDED`：旧 PR/feature SHA 被新 SHA 取代，直接取消。
- `SIDE_EFFECTFUL`：Release/Deploy/Publish，串行且禁止盲目 replay。

Governor v4：`normal cancel -> recheck -> force-cancel`；jobless ghost 不进入代码 Recovery。默认分支已经 in-progress 的正式验证不会因 duplicate 规则被强杀，PR/feature branch 的旧 SHA 可以淘汰。

普通 CI 推荐：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

CI 默认拓扑：Fast Gate（syntax/lint/compile/focused contracts）成功后，再运行 Full Gate（pytest/Docker/Android/Windows/package）。重型任务按改动路径选择执行。

每个仓库只有一个最终 Release/Deploy/Publish authority。artifact/package build 不等于发布。

Node24-native baseline：`actions/checkout@v7`、`setup-python@v7`、`setup-node@v7`、`setup-java@v6`、`upload-artifact@v7`、`download-artifact@v7`。

## 落地清单

1. **GPTWork**：Governor v4、ghost cleanup、Store Package gate、timeout/concurrency。
2. **qnbot**：Fast Gate、去重复 static tests、path gate、Node24 actions。
3. **chat2api**：Governor v4、release gate、contract migration guard。
4. **fdex**：concurrency/timeout、去 push+PR 双触发、path gate、单一 release authority。
