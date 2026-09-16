# GitHub Actions 高频仓库审计与整改（2026-09-16）

对象：`chat2api`、`GPTWork`、`fdex`、`qnbot`。状态：**整改实施中；GPTWork 按用户要求暂停后续改造**。

## 已确认的 GitHub 平台 ghost

GPTWork Governor v4 首次实测扫描 40 个 active run，其中识别出 34 个长期 queued/no-job ghost。它先调用普通 cancel，再调用 GitHub 官方 force-cancel；GitHub 对这些旧 run **两种取消都拒绝**。代表 run：`34749340867`（Store Package）。因此这些历史 run 已不能由仓库内 workflow 自愈，归类为 `GITHUB_PLATFORM_GHOST`；如需从 Actions 后端彻底移除，需要 GitHub 平台侧处理。

为避免 Governor 自己每轮耗费数分钟撞同一批平台 ghost，v4 将每轮 ghost force-cancel 尝试限制为 5 个，并确保同一 pass 不重复尝试。平台 ghost 不进入代码 Recovery，也不计入代码失败率。

## 四仓库整改进度

- **GPTWork**：第一阶段 Governor v4 等治理已落地；后续改造暂停，不作为当前阶段阻塞项。
- **qnbot**：API control plane 已改成 `Fast Gate -> Windows Static Gate -> Full Gate`。Fast Gate 先跑 repository static tests、shell syntax、Python compile、browser JS syntax；重型 pytest/Docker/OCR smoke/package 只在快速检查通过后启动。迁移时同步更新了依赖 workflow 文本的 static contract tests，避免“CI 语义已变、旧测试仍断言旧命令”的确定性红灯。
- **chat2api**：response/runtime contract migration guard 已落地并合并。关键 runtime ownership 文件变化时要求同一变更同步 contract tests；测试若仍实际读取已删除的 `chrome_extension/*.js` 会直接报 `CONTRACT_MIGRATION`，不用等待完整 pytest 才暴露一组重复失败。
- **fdex**：Build and Test 已加入 Path Gate，Android/server 按 diff 独立启动；发布链路收敛为 `main CI success -> Auto Tag -> Release Android APK`，只有 tag-triggered Release workflow 负责签名、APK 构建和 GitHub Release，消除双 release authority。

## 落地过程新增规则

### PR-only policy

只要目标仓库声明 PR-only main policy，GitHub Agent 自身的治理改动也必须走分支 + PR；不能为了修 CI 绕过仓库治理。

### Workflow 也是 contract

如果仓库存在直接读取 `.github/workflows/*.yml` 的 static tests，修改 CI 拓扑时必须在同一 PR 更新这些 contract tests。不能把这类失败误判成 GitHub Runner 故障，也不允许盲目 rerun。

### Android setup Node24

`android-actions/setup-android@v3` 仍以 Node20 为目标；在 GitHub 强制 Node24 后会产生弃用告警。当前使用 `android-actions/setup-android@v4`。此外 v4 默认 `packages` 仍包含已从现代 SDK repository 移除的 `tools`，会导致 `sdkmanager tools` 返回 `Failed to find package 'tools'`。标准写法显式指定：

```yaml
- uses: android-actions/setup-android@v4
  with:
    packages: platform-tools
```

需要的平台/build-tools 再由后续 `sdkmanager` 明确安装。

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

Node24 baseline：`checkout@v7`、`setup-python@v7`、`setup-node@v7`、`setup-java@v6`、`upload-artifact@v7`、`download-artifact@v7`；Android 使用 `android-actions/setup-android@v4` 且显式避开 obsolete `tools` package。

## 当前阶段

1. GPTWork：暂停后续改造。
2. qnbot：Fast Gate/Full Gate 已实施，等待完整重型验证全绿后合并。
3. chat2api：contract migration guard 已通过 Policy Check、专用 Guard 与完整 CI，并已合并。
4. fdex：Path Gate + Single Release Authority 已实施；首次验证发现 `setup-android@v3` / obsolete `tools` 问题，已升级 v4 并显式 `packages: platform-tools`，等待最终 CI 全绿后合并。
