# GitHub Actions 高频仓库深度审计（2026-09-16）

审计对象：`b8vipvip/chat2api`、`b8vipvip/GPTWork`、`b8vipvip/fdex`、`b8vipvip/qnbot`。

状态：**整改实施中**。GitHub Agent v4 标准已在本 PR 中实现第一阶段：Governor force-cancel ghost run、PR-aware concurrency、失败分类、Fast/Full CI 模板、Node24-native action baseline。下一阶段按 `GPTWork -> qnbot -> chat2api -> fdex` 落地到项目仓库。

## 总结

四个仓库当前的 Actions 问题不是单一原因，而是三类问题叠加：

1. **确定性代码/测试失败**：近期代表性红灯多数属于断言、契约或测试与新代码语义不同步；这类问题重跑没有意义。
2. **Workflow 结构放大**：同一个提交同时触发多个重型 workflow、PR 阶段提前做完整打包、重复执行同一套静态测试、缺少 path filter / fast gate / concurrency，使一次代码错误表现成多条红灯并消耗更多 Runner。
3. **GitHub 平台异常残留**：GPTWork 存在长期 `queued` 且无 job 的幽灵 run；Actions Governor v3 已反复尝试普通 cancel，但 GitHub API 拒绝取消。最早一批 run 创建于 2026-09-13 09:20 UTC，时间与 GitHub 官方同日 Actions degraded performance 事故窗口高度重合。

因此，v4 同时解决 **代码失败分类、Workflow 拓扑、平台幽灵 run**，不再采用“失败就 rerun”的简单策略。

## 1. chat2api

- CI 已有 PR 级 concurrency、timeout、pytest timeout，基础治理较完整。
- 最新代表性失败是确定性测试失败：Runner、checkout、Python/Node setup、依赖安装、语法检查均成功，pytest 最后因 response terminal owner / preflight / recovery contract 与旧回归测试不同步而失败。
- `production-image-smoke.yml` 含大量硬编码版本/字符串契约，架构迁移时必须与代码同提交更新。
- `release.yml` 通过轮询等待 CI / smoke，后续应改事件式 gate，减少等待 Runner。
- 仍存在历史 queued run，Governor v4 用 normal cancel -> recheck -> force-cancel 处理。

## 2. GPTWork

### 关键问题

- GitHub API 当前可见多批长期 `queued`、无 job 的 ghost run。
- v3 Governor 扫描这些 active run 后，普通 cancel 被 GitHub 拒绝，导致长期残留。
- `Store Package` 在 PR 上过早启动 Windows + Linux 完整打包。
- v3 按名称把 Store Package 误判为 release 类副作用 workflow；v4 已移除该误判。
- `Private Core Boundary`、`license-server`、housekeeping/cleanup 等存在缺 timeout/concurrency 的情况。

### v4 对策

- queued + no jobs + 超过阈值 => `GHOST_RUN`。
- normal cancel 后重新读取状态，仍 active => `/force-cancel`。
- ghost run 清理后不进入代码 Recovery。
- Store Package 改为普通 artifact build，PR 可被新 SHA 取代；并延后到 Fast/CI gate 成功后执行。

## 3. fdex

- 代表性失败为 FastAPI pytest 的 UI/CSS contract 与新实现不同步，Android job 本身成功。
- feature/fix/agent 分支 push + pull_request 可能让同一提交重复触发 CI。
- FastAPI 与 Android build 缺 path-aware gate。
- `release.yml` 与 `auto-tag-release.yml` 发布职责需要收敛成单一 Release authority。

## 4. qnbot

- PR #277 的同一提交同时触发 API control plane CI 与 Windows x64 release build，两个 workflow 重复运行 repository static tests，并因同一个旧 UI contract assertion 一起失败。
- 这类结构会把一个代码错误放大成多条红灯。
- API-only 改动仍可能启动完整 Windows/MSBuild/package，缺 path-aware gate。
- 多个 workflow 缺 concurrency/timeout。
- 旧 action major 需要迁移到 Node24-native 版本。

## GitHub Agent v4 已实现的标准

### A. 失败分类

- `DETERMINISTIC_TEST`：pytest / assertion / compile / lint；禁止自动 rerun。
- `WORKFLOW_CONFIG`：YAML / action / permission；修 workflow 后新 commit 验证。
- `INFRA_TRANSIENT`：Runner lost、DNS、连接重置、502/503/504；最多一次 fresh rerun。
- `GHOST_RUN`：长期 queued/in_progress、无 job 或 normal cancel 无效；force-cancel。
- `SUPERSEDED`：被新 SHA 取代；直接 cancel。
- `SIDE_EFFECTFUL`：Release / Deploy / Publish；串行且禁止盲目 replay。

### B. Governor v4

- normal cancel -> recheck -> force-cancel。
- queued 且无 job 的 stale run 视为 `GHOST_RUN`，不进入 Recovery。
- 默认分支已经 in-progress 的正式验证不会因 duplicate 规则被强杀。
- PR/feature branch 的旧 SHA 可积极淘汰。

### C. Concurrency v4

推荐普通 CI：

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

Release / Deploy / Publish：串行，`cancel-in-progress: false`。

### D. Fast Gate -> Full Gate

1. Fast Gate：syntax / lint / compile / contract / changed-scope tests。
2. Full Gate：完整 pytest / Docker / Windows build / installers / package。

Full Gate 只有 Fast Gate 成功后才运行。

### E. Path-aware CI

- Python/API 改动不启动无关 Android/Windows installer。
- Android/desktop 改动不启动无关服务端 full suite。
- 文档改动默认不启动完整构建。

### F. 单一发布 authority

一个仓库只能有一个 workflow 拥有创建/覆盖 tag、GitHub Release、production deploy 的最终权限。其他 workflow 只生产 artifact 或显式调用发布 workflow。

### G. Node24-native Actions

v4 模板基线：

- `actions/checkout@v7`
- `actions/setup-python@v7`
- `actions/setup-node@v7`
- `actions/setup-java@v6`
- `actions/upload-artifact@v7`
- `actions/download-artifact@v7`

## 落地顺序

1. **GPTWork**：Governor v4 + ghost cleanup + Store Package gate + timeout/concurrency。
2. **qnbot**：Fast Gate、去重复 static tests、path gate、Node24 actions。
3. **chat2api**：Governor v4、release event gate、contract migration guard。
4. **fdex**：concurrency/timeout、去 push+PR 双触发、path gate、单一 release authority。
