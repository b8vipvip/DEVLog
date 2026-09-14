# GitHub Actions 策略 v2.0

## 目标

GitHub Actions 的问题不能只靠一份“模板”解决。真正稳定的做法必须同时覆盖：新项目预防、老项目迁移、运行中资源治理、历史异常任务清理，以及策略落地后的验收。

## 强制规则

### 1. 自动 CI / Test / Smoke 必须取消旧运行

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

同一 PR 或同一 ref 产生新运行后，旧运行应立即退出，不能继续占用 Runner。

### 2. 核心 Job 必须设置显式超时

建议范围：

- Lint / 单元测试：10～20 分钟
- Docker / 构建 / Smoke：20～45 分钟
- Release / Deploy：可以更长，但不能无限运行

Python pytest 应另外配置单测试超时，例如 `pytest-timeout`，避免一个测试死锁拖死整个 Job。

### 3. 权限最小化

普通 CI 默认使用：

```yaml
permissions:
  contents: read
```

只有仓库级治理工作流需要 `actions: write`；只有发布任务需要 `contents: write`。

### 4. 临时 Debug Workflow 必须手动触发

临时诊断完成后必须改成：

```yaml
on:
  workflow_dispatch:
```

并设置较短的 `timeout-minutes`。禁止 Debug Workflow 长期跟随所有 push / PR 自动运行。

### 5. Release / Deploy 是受控例外

Release / Deploy / Publish / Store Package 可以使用：

```yaml
cancel-in-progress: false
```

因为发布过程通常不应该被新提交直接打断，但它们必须：

- 使用独立串行 concurrency group；
- 仍然受仓库级 Governor 180 分钟硬上限保护；
- 不得无限等待其它 Workflow。

## Actions Governor：仓库级强制治理

每个需要长期运行 Actions 的项目都应部署 `.github/workflows/actions-governor.yml`。

Governor 每 10 分钟扫描仍处于 `in_progress` 或 `queued` 的运行，并执行两层治理。

### 第一层：重复运行清理

对普通工作流，以 `workflow name + head branch + event` 为键，只保留最新一条活动运行，旧的重复运行自动取消。

这可以解决：

- 同一 PR 在短时间内连续提交多次；
- CI #1735、#1736、#1737、#1738 同时运行；
- 旧 Commit 的测试仍然占 Runner，而新 Commit 已经开始测试。

### 第二层：异常长运行清理

默认硬上限：

- 普通工作流：45 分钟；
- Release / Deploy / Publish / Store Package：180 分钟。

达到阈值仍未结束时，Governor 调用 GitHub Actions Cancel API 自动取消。

### 历史任务兼容

Governor 查询的是仓库“当前仍在运行的任务”，而不是只管理策略启用后的任务。因此：

- 策略启用前已经卡住一小时的 CI；
- 旧 YAML 启动的任务；
- 没有 `timeout-minutes` 的历史运行；

都可以被新 Governor 识别并取消。

这正是老项目事故恢复与新项目预防的连接点。

## 老项目标准迁移顺序

1. 新增 Actions Governor。
2. 给主 CI / Test / Smoke 增加 concurrency 与 `cancel-in-progress: true`。
3. 给核心 Job 增加 `timeout-minutes`。
4. 给 pytest / 测试框架增加单测试超时。
5. 临时 Debug Workflow 改为手动触发。
6. Release / Deploy 使用独立串行 concurrency group。
7. 合并策略后，让 Governor 自动清理历史异常运行。
8. 再触发一轮正式 CI，确认只剩最新一代运行。

## 新项目标准接入顺序

新仓库第一次建立 Actions 时直接套用本目录模板：

1. `templates/ci.yml`
2. `templates/actions-governor.yml`
3. 有临时排障时使用 `templates/debug.yml`
4. 有发布需求时使用 `templates/release.yml`

## 验收标准

只有以下条件全部满足，才能认为策略真正生效：

- 同一 PR 连续 push 两次，旧 CI 自动 `cancelled`。
- 普通 CI 不会无限运行，仓库级最大 45 分钟。
- 发布类工作流最大 180 分钟。
- 单个测试死锁不会拖死整个 Job。
- 策略启用之前遗留的长时间运行任务可以自动清掉。
- 临时 Debug 不再随所有 push / PR 自动触发。
- 最新正式运行最终明确显示 `success`、`failure`、`cancelled` 或 `timed_out`，而不是长期 `in_progress`。

## 禁止事项

- 不允许为了“看它会不会自己结束”让已确认异常的 CI 连续运行数小时。
- 不允许同一 PR 的多代 CI 同时长期占用 Runner。
- 不允许用反复 Re-run 代替根因修复。
- 不允许把一次性 Debug Workflow 永久保留为自动触发。
- 不允许 Release 任务没有任何资源上限。
