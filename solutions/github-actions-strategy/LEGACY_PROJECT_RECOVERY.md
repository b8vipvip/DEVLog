# 老项目 GitHub Actions 恢复与迁移 SOP

本 SOP 用于已经出现以下现象的仓库：同一 PR 多代 CI 同时运行、某个测试长时间不返回、Actions 列表里存在一小时以上仍为 `in_progress` 的旧任务、临时 Workflow 数量过多、Runner 被历史任务持续占用。

## A. 先止损

1. 不再继续手工反复 Re-run。
2. 加入 `actions-governor.yml`。
3. Governor 合并到主分支后，立即执行一次，并持续每 10 分钟执行。
4. 普通活动任务超过 45 分钟自动取消；发布类超过 180 分钟自动取消。
5. 同一普通 workflow + branch + event 只保留最新活动任务。

Governor 能清理策略落地之前启动的任务，因此不需要等待历史异常任务自己结束。

## B. 再修主 Workflow

对 CI / Test / Smoke：

```yaml
permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  test:
    timeout-minutes: 20
```

如果是 pytest：

```bash
python -m pip install pytest-timeout
pytest -q --timeout=120
```

如果是 npm / cargo / Docker 等，也必须通过 Job 级 `timeout-minutes` 提供上限。

## C. 清理临时诊断 Workflow

排障时创建的临时 Workflow 完成使命后必须改成：

```yaml
on:
  workflow_dispatch:
```

或直接删除。禁止长期保留为 `push` / `pull_request` 自动触发。

## D. 处理 Release / Deploy

发布任务一般不使用 `cancel-in-progress: true`，避免正在发布时被下一次提交打断。推荐：

```yaml
concurrency:
  group: project-release
  cancel-in-progress: false
```

同时仍由 Governor 提供 180 分钟硬上限。

## E. 验收

迁移完成后做一次并发验证：

1. 在同一测试分支连续 push 两个很小的提交。
2. 第二次 CI 开始后，第一次 CI 应自动变为 `cancelled`。
3. 检查 Actions 页面只保留最新一代普通 CI 继续运行。
4. 人为制造一个可控的等待测试时，应在测试级或 Job 级超时被终止。
5. 检查 Governor 运行日志，确认能够扫描活动任务并输出取消原因。

## chat2api / GPTWork 案例

- chat2api 曾出现同一 PR 的多条 CI 同时保持 `in_progress`，并有运行超过一小时的 pytest 任务；这类历史任务应由 Governor 自动清理。
- GPTWork 的问题更多表现为真实测试失败，而不是无限运行；策略负责防止失败任务演化成资源堆积，但不会把真实代码错误“自动变绿”。
