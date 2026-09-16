# GitHub Actions 高频仓库审计与整改（2026-09-16）

对象：`chat2api`、`GPTWork`、`fdex`、`qnbot`。状态：**整改实施中**。

## 已确认的 GitHub 平台 ghost

GPTWork Governor v4 首次实测扫描 40 个 active run，其中识别出 34 个长期 queued/no-job ghost。它先调用普通 cancel，再调用 GitHub 官方 force-cancel；GitHub 对这些旧 run **两种取消都拒绝**。代表 run：`34749340867`（Store Package）。因此这些历史 run 已不能由仓库内 workflow 自愈，归类为 `GITHUB_PLATFORM_GHOST`；如需从 Actions 后端彻底移除，需要 GitHub 平台侧处理。

为避免 Governor 自己每轮耗费数分钟撞同一批平台 ghost，v4 将每轮 ghost force-cancel 尝试限制为 5 个，并确保同一 pass 不重复尝试。平台 ghost 不进入代码 Recovery，也不计入代码失败率。

## 四仓库整改进度

- **GPTWork**：Governor v4 已落地；Store Package 已增加 path filter、PR-aware concurrency、timeout 和 Node24-native actions；License Server、Private Core Boundary 已补 timeout/concurrency/手动恢复入口。历史平台 ghost 保留为平台异常证据。
- **qnbot**：Windows release build 已移除与 API CI 重复的 repository static tests，加入 path filter、PR-aware concurrency、timeout、Node24-native actions；Windows CI 同步升级，两次对应 Actions 已验证成功。
- **chat2api**：Governor v4 已落地且对应 Actions 验证成功；后续重点是 contract migration guard 与 release gate 优化。
- **fdex**：主 CI 已去掉 feature/fix/agent push + PR 双触发，改为 main push + PR，加入 PR-aware concurrency、timeout、Node24-native actions；对应 Android/FastAPI CI 已验证成功。

## 落地过程新增规则

GPTWork 自身有 `Repository housekeeping -> Audit PR-only main changes`。直接写 main 的 GitHub Agent 维护提交会被该策略正确标红。因此从本轮后续开始，**只要目标仓库声明 PR-only main policy，GitHub Agent 自身的治理改动也必须走分支 + PR；不能为了修 CI 绕过仓库自己的治理策略。** 这条规则纳入 v4。

## v4 分类

`DETERMINISTIC_TEST`、`WORKFLOW_CONFIG`、`INFRA_TRANSIENT`、`GHOST_RUN`、`GITHUB_PLATFORM_GHOST`、`SUPERSEDED`、`SIDE_EFFECTFUL`。

Governor：`normal cancel -> recheck -> force-cancel`；force-cancel 仍被 GitHub 拒绝则标记 `GITHUB_PLATFORM_GHOST` 并限流。默认分支已经 in-progress 的正式验证不因 duplicate 被强杀。

普通 CI：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

CI：Fast Gate 成功后再运行完整 pytest/Docker/Android/Windows/package，并按改动路径选择重型任务。发布 workflow 使用单一最终 authority；artifact/package build 不等于发布。

Node24 baseline：`checkout@v7`、`setup-python@v7`、`setup-node@v7`、`setup-java@v6`、`upload-artifact@v7`、`download-artifact@v7`。

## 下一阶段

1. GPTWork：后续治理改动改走 PR；继续收敛 housekeeping/release 触发面。
2. qnbot：继续拆 API Fast Gate 与重型 build path gate。
3. chat2api：增加 contract migration guard，优化 release event gate。
4. fdex：Android/server path gate 与单一 release authority。
