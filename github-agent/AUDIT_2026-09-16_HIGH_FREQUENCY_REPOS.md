# GitHub Actions 高频仓库审计与整改（2026-09-16）

对象：`chat2api`、`GPTWork`、`fdex`、`qnbot`。状态：**整改实施中**。

## 结论

近期红灯由三类问题叠加：确定性代码/测试失败、Workflow 拓扑放大、GitHub 平台 ghost run 残留。GitHub Agent v4 已完成标准层整改：失败分类、PR-aware concurrency、Fast Gate -> Full Gate、path-aware heavy builds、Governor ghost handling、Single Release Authority、Node24-native baseline。

### 已确认的 GitHub 平台 ghost

GPTWork Governor v4 首次实测扫描 40 个 active run，其中识别出 34 个长期 queued/no-job ghost。它先调用普通 cancel，再调用 GitHub 官方 force-cancel；GitHub 对这些旧 run **两种取消都拒绝**。代表 run：`34749340867`（Store Package）。因此这些历史 run 已不能由仓库内 workflow 自愈，属于 `GITHUB_PLATFORM_GHOST`；如需从 Actions UI/后端彻底移除，需要 GitHub 平台侧处理。

为避免 Governor 自己每 10 分钟耗费数分钟反复撞同一批平台 ghost，v4 模板将每轮 ghost force-cancel 尝试限制为 5 个，并确保同一 pass 不重复尝试。平台 ghost 不进入代码 Recovery，也不计入代码失败率。

## 四仓库整改重点

- **GPTWork**：Governor v4 已落地；Store Package 已增加 path filter、PR-aware concurrency、timeout 和 Node24-native actions；License Server、Private Core Boundary 已补 timeout/concurrency/手动恢复入口。历史平台 ghost 保留为平台异常证据。
- **qnbot**：Windows release build 已移除与 API CI 重复的 repository static tests，加入 path filter、PR-aware concurrency、timeout、Node24-native actions；Windows CI 同步升级。
- **chat2api**：Governor v4 已落地并验证成功；后续重点仍是 contract migration guard 与 release gate 优化。
- **fdex**：主 CI 已去掉 feature/fix/agent push + PR 双触发，改为 main push + PR，加入 PR-aware concurrency、timeout、Node24-native actions；后续继续做 path-aware Android/server gate 与 release authority 收敛。

## v4 规则

失败分类：`DETERMINISTIC_TEST`、`WORKFLOW_CONFIG`、`INFRA_TRANSIENT`、`GHOST_RUN`、`GITHUB_PLATFORM_GHOST`、`SUPERSEDED`、`SIDE_EFFECTFUL`。

Governor：`normal cancel -> recheck -> force-cancel`。如果 force-cancel 仍被 GitHub 拒绝，则标记 `GITHUB_PLATFORM_GHOST` 并限流，不进入代码 Recovery。默认分支已经 in-progress 的正式验证不因 duplicate 被强杀。

普通 CI：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

CI：Fast Gate 成功后再运行完整 pytest/Docker/Android/Windows/package，并按改动路径选择重型任务。

发布：每个仓库只有一个最终 Release/Deploy/Publish authority；artifact/package build 不等于发布。

Node24 baseline：`checkout@v7`、`setup-python@v7`、`setup-node@v7`、`setup-java@v6`、`upload-artifact@v7`、`download-artifact@v7`。

## 下一阶段

1. GPTWork：继续收敛 housekeeping/release 触发面，避免 workflow-only commit 启动无关 Release。
2. qnbot：继续拆 API Fast Gate 与重型 build path gate。
3. chat2api：增加 contract migration guard，优化 release event gate。
4. fdex：Android/server path gate 与单一 release authority。
