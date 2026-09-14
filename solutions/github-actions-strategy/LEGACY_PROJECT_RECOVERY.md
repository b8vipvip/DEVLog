# 老项目 GitHub Actions 恢复与迁移 SOP（Strategy v3）

本 SOP 用于已经出现同一 PR 多代 CI 同时运行、pytest/npm/cargo/Docker 长时间不返回、历史 `in_progress` / `queued` 任务占用资源、临时 Workflow 泛滥等问题的仓库。

## A. 先部署 v3 控制面

必须先加入：

- `.github/workflows/actions-governor.yml`
- `.github/workflows/actions-recovery.yml`
- `.github/workflows/actions-policy-check.yml`
- `.github/scripts/actions_strategy_autofix.py`
- `.github/scripts/validate_actions_strategy.py`
- `.github/ACTIONS_STRATEGY.md`

Governor 每 10 分钟扫描，普通任务 45 分钟上限，发布类 180 分钟上限。

## B. 历史卡死任务不能只 Cancel

Strategy v3 的历史恢复必须遵循：

```text
stale run
  ↓
Governor Cancel，先释放 Runner
  ↓
Recovery 收集 metadata + logs
  ↓
自动修复 Workflow 策略缺陷
  ↓
可选项目级 actions-recovery.sh
  ↓
Recovery branch / PR
  ↓
普通 Workflow 对修复 ref 重新 dispatch
  ↓
若没有修改，只允许 fresh rerun 1 次
  ↓
仍不能恢复则自动创建 Recovery Issue
```

如果旧任务已经被更新 Commit 替代，则只取消旧 duplicate，因为新运行已经完成“重新提交”，禁止复活过时代码。

## C. 项目级自动修复 Hook

仓库可添加：

```text
.github/actions-recovery.sh
```

Recovery 会从当前默认分支读取这个 hook，并在异常任务的源代码工作区执行。可以使用这些环境变量：

- `ACTIONS_RECOVERY_LOG`：源 run 日志文件；
- `SOURCE_RUN_ID`；
- `SOURCE_WORKFLOW_NAME`；
- `SOURCE_BRANCH`；
- `RECOVERY_REASON`。

Hook 必须满足：

1. **确定性**：只修复已经明确识别的故障模式；
2. **幂等**：执行两次不会不断产生新改动；
3. **最小修改**：不得趁恢复流程顺便做无关重构；
4. **可验证**：修改后由 Recovery 分支/PR 和重新 dispatch 验证。

适合自动编码的例子：已知 fixture 状态缺失、生成文件未同步、固定配置迁移、锁文件恢复、某类缓存/临时文件清理。全新业务逻辑错误不应由 shell 脚本猜测修复。

## D. 主 Workflow 迁移

普通 CI/Test/Smoke：

```yaml
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  test:
    timeout-minutes: 20
```

pytest 应再增加单测试 timeout，例如 `pytest -q --timeout=120`。

## E. Debug Workflow

Debug/diagnostic/one-shot/tmp Workflow 排障结束后只能保留 `workflow_dispatch`，禁止长期随 push / pull_request 自动执行。

## F. Release / Deploy

发布类不能盲目自动重放，因为可能造成重复发布/部署：

```yaml
concurrency:
  group: project-release
  cancel-in-progress: false
```

Governor 仍提供 180 分钟上限。Recovery 可以修 Workflow、提交 PR、建立 Incident，但真正再次发布需要明确批准。

## G. 验收

迁移完成后验证：

1. 同一 PR 连续 push，两代普通 CI 中旧任务应自动取消。
2. Policy Check 对新增/修改 Workflow 生效。
3. 人为制造可控等待，Job/test timeout 能终止。
4. Governor 能看到并清理历史 stale run。
5. stale run 被清理后能看到 Actions Recovery 被 dispatch。
6. 人为准备一个缺少 timeout/concurrency 的测试 Workflow，Recovery 应能生成修复 branch/PR。
7. 可恢复普通 Workflow 应能在修复 ref 上重新 dispatch。
8. 无修复内容的异常 run 最多自动 rerun 一次；再次异常应生成 Recovery Issue，而不是无限循环。
