# GitHub Actions 高频仓库深度审计（2026-09-16）

审计对象：`b8vipvip/chat2api`、`b8vipvip/GPTWork`、`b8vipvip/fdex`、`b8vipvip/qnbot`。

目标：为 GitHub Agent / GitHub Actions 标准模板下一版提供真实仓库证据，不再只做“缺 concurrency / timeout”这一类静态检查。

## 总结

四个仓库当前的 Actions 问题不是单一原因，而是三类问题叠加：

1. **确定性代码/测试失败**：近期代表性红灯多数属于断言、契约或测试与新代码语义不同步；这类问题重跑没有意义。
2. **Workflow 结构放大**：同一个提交同时触发多个重型 workflow、PR 阶段提前做完整打包、重复执行同一套静态测试、缺少 path filter / fast gate / concurrency，使一次代码错误表现成多条红灯并消耗更多 Runner。
3. **GitHub 平台异常残留**：GPTWork 存在 34 个长期 `queued` 且无 job 的幽灵 run；Actions Governor v3 已反复尝试普通 cancel，但 GitHub API 拒绝取消。最早一批 run 创建于 2026-09-13 09:20 UTC，时间与 GitHub 官方 09:16 起的多服务事故、09:25 明确报告 Actions degraded performance 高度重合。

因此，下一版标准必须同时解决 **代码失败分类、Workflow 拓扑、平台幽灵 run**，不能只靠“失败就 rerun”。

## 1. chat2api

### 当前结构

主要 workflow：

- `ci.yml`
- `production-image-smoke.yml`
- `release.yml`
- `actions-governor.yml`
- `actions-recovery.yml`
- `actions-policy-check.yml`

### 发现

- CI 已有 PR 级 concurrency、timeout、pytest timeout，基础治理在四个仓库中较完整。
- 最新代表性失败仍是确定性测试失败：Runner、checkout、Python/Node setup、依赖安装、语法检查均成功，最后 pytest 出现多项 assertion failure；根因是 response terminal owner / preflight / recovery contract 已变化，但旧回归测试仍要求旧 owner / 旧脚本 / 旧输出语义。
- `production-image-smoke.yml` 含大量硬编码版本/字符串契约。架构迁移时如果代码与 smoke contract 不在同一提交同步更新，会产生第二条独立红灯。
- `release.yml` 通过轮询等待 CI / smoke 结果，最长约 15 分钟。虽然可工作，但会占用 Runner；下一版应优先使用事件式 gate，而不是启动 release job 后等待。
- 当前仍存在一个从 2026-08-19 起保持 `queued` 的历史 CI run，说明 Governor v3 的普通 cancel 不能清理所有幽灵状态。

### 结论

chat2api 的主要问题已经从“Actions 基础治理缺失”转为 **契约迁移纪律 + 幽灵 run 清理 + release gate 优化**。

## 2. GPTWork

### 当前结构

主要 workflow：

- `ci.yml`
- `private-core-boundary.yml`
- `store-package.yml`
- `license-server.yml`
- `release.yml`
- `repository-housekeeping.yml`
- `release-asset-cleanup.yml`
- GitHub Agent v3 三件套

### 关键发现：34 个幽灵 queued run

当前 GitHub API 返回 **34 个 queued run**。代表 run：

- Store Package run `34749340867`
- 创建时间：2026-09-13 09:20:24 UTC
- 状态：`queued`
- jobs：空

Actions Governor v3 的最新定时运行扫描到 34 个 active run，并对 CI、Private Core Boundary、Store Package 等逐个调用普通 cancel，但全部出现：

`could not be cancelled; it may already have completed`

最终结果：

`Active runs scanned: 34; cancelled: 0; recovery dispatched: 0.`

这说明 v3 缺少 **normal cancel -> recheck -> force-cancel** 的第二级清理链路。

### Workflow 结构问题

- `Store Package` 在每个 PR 上直接启动 Windows + Linux 完整打包，即使普通 CI 尚未通过。
- `Store Package` 被 v3 按名称误判为 release 类“受保护副作用 workflow”，使用 `cancel-in-progress: false`。但它本质上只是构建 artifact，并不等同于发布到生产环境。
- `Private Core Boundary` 当前没有 workflow concurrency，也没有 job timeout。
- `license-server.yml` 没有 concurrency / timeout。
- `repository-housekeeping.yml`、`release-asset-cleanup.yml`、多个 release job 缺少 job timeout。
- `release.yml` 启动后轮询 CI / Store Package / Private Core Boundary / housekeeping，最长等待约 15 分钟，同样会占用 Runner。

### 结论

GPTWork 是本轮优先级最高的仓库。它同时存在 **GitHub 平台幽灵状态 + v3 Governor 清理能力不足 + PR 阶段重型打包过早 + 多 workflow 缺 timeout/concurrency**。

## 3. fdex

### 当前结构

- `ci.yml`
- `auto-tag-release.yml`
- `release.yml`

### 发现

- 最近代表性失败中，Android Debug APK 成功，FastAPI Tests 失败；失败发生在 pytest，而不是 Runner / checkout / setup。
- 失败属于 UI/CSS 契约断言与新实现不同步，属于确定性代码/测试问题。
- `ci.yml` 没有 workflow concurrency，也没有 job timeout。
- `ci.yml` 同时监听 `push` 的 `agent/**`、`feature/**`、`fix/**`、`chore/**` 和 `pull_request: main`。当这些开发分支同时打开 PR 时，可能为同一提交产生 push + PR 两套 CI。
- FastAPI 与 Android 构建无 path-aware gate；仅改服务端也会启动 Android，反之亦然。
- `release.yml` 与 `auto-tag-release.yml` 都具备创建 GitHub Release 的能力，形成双发布入口。即使 `GITHUB_TOKEN` 生成的 tag 通常不会再次触发 push workflow，发布职责仍应收敛为单一 authority，避免人工 tag / workflow_dispatch 时产生两套发布语义。

### 结论

fdex 当前平台状态最干净，但 Workflow 仍属于旧式“全量触发”结构。重点是 **去双触发、按路径拆分、单一 Release authority、补 concurrency/timeout**。

## 4. qnbot

### 当前结构

- `api-control-plane-ci.yml`
- `build-windows.yml`
- `windows-build.yml`
- `publish-bot-auto-update-release.yml`
- `publish-bot-rescue-asset.yml`

### 代表性失败

PR #277 的提交 `39eabd9...` 同时触发：

- `API control plane CI` -> failure
- `Windows x64 release build` -> failure

两个 workflow 都在 `Run repository static tests` 失败；同一个确定性 assertion 被重复执行，因此一个代码错误在 Actions 页面表现为至少两条红灯。

具体断言：测试仍要求旧的 `Session Desk` 表格表头，而模板已改为 `Owner Account / Desk Slot` 语义。该轮测试达到 `1070 passed, 1 failed`，说明不是 Runner 故障。

### Workflow 结构问题

- `api-control-plane-ci.yml` 没有 concurrency / timeout。
- 它同时监听多个 feature push 与 pull_request，存在 push + PR 重复执行风险。
- `windows-build.yml` 没有 concurrency / timeout。
- `build-windows.yml` 虽有 concurrency / timeout，但 `cancel-in-progress: true` 同样作用于 master push，会取消正在进行的正式 master 验证。
- `API control plane CI` 与 `Windows x64 release build` 都重复运行 repository static tests，应该抽成 Fast Gate，只运行一次。
- API-only 改动仍会启动完整 Windows Release/MSBuild/package 构建；缺少 path-aware gate。
- `publish-bot-auto-update-release.yml`、`publish-bot-rescue-asset.yml` 缺少 job timeout。
- Rescue workflow 使用“latest release”语义，若仓库未来存在非 Bot release，可能把 rescue asset 附加到错误 release；应显式选择最新 `bot-v*` release。
- 多个 workflow 仍使用 `actions/checkout@v4`、`actions/setup-python@v5`、`actions/upload-artifact@v4`。2026-09 GitHub Runner 已迁移 Node 24，并将在 2026-09-23 移除 Node 20；这些旧 action 已出现强制 Node24/弃用警告，应升级到 Node24-native major。

### 结论

qnbot 的主要问题是 **同一提交重复跑重型 workflow + 同一静态测试重复执行 + 缺 path gate/concurrency/timeout + Actions Node24 迁移债务**。

## GitHub Agent v4 必须新增的规则

### A. 失败分类

统一分类：

- `DETERMINISTIC_TEST`：pytest / unit test / assertion / compile / lint 明确失败；禁止自动 rerun。
- `WORKFLOW_CONFIG`：YAML / action / permission / invalid workflow；修 workflow 后新 commit 验证。
- `INFRA_TRANSIENT`：Runner lost、DNS、连接重置、502/503/504；最多一次 fresh rerun。
- `GHOST_RUN`：长期 queued/in_progress、无 job 或 normal cancel 无效；进入 force-cancel 链路。
- `SUPERSEDED`：被新 SHA 取代；直接 cancel，不 recovery。
- `SIDE_EFFECTFUL`：Release / Deploy / Publish；禁止盲目 replay。

### B. Governor v4

- normal cancel 失败后重新读取 run 状态；若仍 active，调用 `/force-cancel`。
- queued 且无 job 的 stale run 视为 `GHOST_RUN`，清理后不进入代码 Recovery。
- 只有真正执行过 job 的失败/卡死 run 才进入 Recovery / AI Repair Brief。
- `Store Package` / 普通 artifact build 不再按名称自动视为生产副作用任务。

### C. Concurrency v4

- PR：同 PR 只保留最新 SHA，`cancel-in-progress: true`。
- 默认分支 push：不取消已经运行的正式 CI；允许 GitHub 默认只保留一个 pending 最新 run。
- Release / Deploy / Publish：串行，`cancel-in-progress: false`。
- 不再用“所有普通 workflow 都必须 true”的简单规则。

### D. Fast Gate -> Full Gate

高频仓库默认两层：

1. Fast Gate：syntax / lint / compile / contract / changed-scope tests。
2. Full Gate：完整 pytest / Docker / Windows build / installers / package。

Full Gate 只有 Fast Gate 成功后才运行。

### E. Path-aware CI

- Python/API 改动不启动 Android/Windows installer。
- Android 改动不启动无关 FastAPI full suite。
- 文档改动不启动完整构建，除非文档本身是产品 artifact。

### F. 单一发布 authority

一个仓库只能有一个 workflow 拥有创建/覆盖 tag、GitHub Release、production deploy 的最终权限。其他 workflow 只能生产 artifact 或显式调用该发布 workflow。

### G. Node24-native Actions

2026-09 起标准模板应优先使用当前 Node24-native major，例如：

- `actions/checkout@v7`
- `actions/setup-python@v7`
- `actions/setup-node@v7`
- `actions/setup-java@v6`
- `actions/upload-artifact@v7`
- `actions/download-artifact@v7`

项目升级时需检查第三方 action 是否也已兼容 Node24。

## 建议落地顺序

1. **GPTWork**：先清理 ghost queued run，并修 Governor v4 / Store Package gate。
2. **qnbot**：抽 Fast Gate，去重复 static tests，按路径控制 Windows/API 重型任务，升级 Node24 actions。
3. **chat2api**：升级 Governor v4、release event gate、契约迁移检查。
4. **fdex**：补 concurrency/timeout、去 push+PR 双触发、path gate、单一 release authority。

四仓库全部落地后，再把通用规则回灌到 DEVLog 模板和 validator，形成可复制的 GitHub Agent v4。