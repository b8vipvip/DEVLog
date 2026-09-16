# GitHub Actions 高频仓库审计与整改（2026-09-16）

对象：`chat2api`、`GPTWork`、`fdex`、`qnbot`。状态：**整改实施中**。

## 结论

近期红灯由三类问题叠加：确定性代码/测试失败、Workflow 拓扑放大、GitHub 平台 ghost run 残留。GitHub Agent v4 已完成标准层整改：失败分类、PR-aware concurrency、Fast Gate -> Full Gate、path-aware heavy builds、Governor force-cancel、Single Release Authority、Node24-native baseline。

- **GPTWork**：最高优先级。长期 queued 且无 job 的 ghost runs；v3 普通 cancel 无法清理；Store Package 过早启动并被误判为 release 类；多个 workflow 缺 timeout/concurrency。
- **qnbot**：同一提交在 API CI 与 Windows build 重复跑 static tests，一个 assertion failure 被放大成多条红灯；缺 path gate/concurrency/timeout；旧 action major 待迁移。
- **chat2api**：基础治理较完整；重点是 contract migration guard、历史 ghost cleanup 和 release gate 优化。
- **fdex**：重点是去 push+PR 双触发、path gate、timeout/concurrency 和单一 release authority。

## v4 规则

失败分类：`DETERMINISTIC_TEST`、`WORKFLOW_CONFIG`、`INFRA_TRANSIENT`、`GHOST_RUN`、`SUPERSEDED`、`SIDE_EFFECTFUL`。

Governor：`normal cancel -> recheck -> force-cancel`；jobless ghost 不进入代码 Recovery；默认分支已经 in-progress 的正式验证不因 duplicate 被强杀。

普通 CI：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

CI：Fast Gate 成功后再运行完整 pytest/Docker/Android/Windows/package，并按改动路径选择重型任务。

发布：每个仓库只有一个最终 Release/Deploy/Publish authority；artifact/package build 不等于发布。

Node24 baseline：`checkout@v7`、`setup-python@v7`、`setup-node@v7`、`setup-java@v6`、`upload-artifact@v7`、`download-artifact@v7`。

## 落地顺序

1. GPTWork：Governor v4 + ghost cleanup + Store Package gate + timeout/concurrency。
2. qnbot：Fast Gate + 去重复 static tests + path gate + Node24 actions。
3. chat2api：Governor v4 + release gate + contract migration guard。
4. fdex：concurrency/timeout + 去双触发 + path gate + 单一 release authority。
