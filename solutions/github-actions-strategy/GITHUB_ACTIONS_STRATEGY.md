# GitHub Actions 策略 v3

## 目标

v3 把 GitHub Actions 治理从“模板”升级为持续运行的策略系统，覆盖：

- 新项目预防；
- 老项目迁移；
- 同 PR 多代 CI 自动去重；
- 测试/构建超时；
- 历史卡死任务自动恢复；
- 自动修复可确定的 Workflow 问题；
- 修复后自动重新提交；
- 自动修复无法继续时留下 Recovery Incident。

## 1. Workflow Guard

普通 CI / Test / Smoke 必须：

```yaml
permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

每个 `runs-on` Job 必须有 `timeout-minutes`。推荐：

- Lint / 单元测试：10～20 分钟；
- Docker / 构建 / Smoke：20～45 分钟；
- Windows 大型安装器验证：30～45 分钟。

可恢复 Workflow 应保留 `workflow_dispatch`，以便 Recovery 对修复后的 ref 显式重新提交。

Release / Deploy / Publish / Store Package 属于有副作用任务，使用独立串行 concurrency group、`cancel-in-progress: false`，但最长不能超过 180 分钟。

## 2. Actions Policy Check

部署 `.github/workflows/actions-policy-check.yml` 与 `.github/scripts/validate_actions_strategy.py`。

Policy Check 对新增/修改 Workflow 强制检查：

- 明确 `permissions`；
- 明确 `concurrency`；
- 普通任务 `cancel-in-progress: true`；
- 发布类 `cancel-in-progress: false`；
- Job 显式 timeout；
- `workflow_dispatch` 恢复入口；
- Debug / diagnostic / one-shot / tmp Workflow 只能手动运行。

老 Workflow 可以分阶段迁移，但只要再次修改，就必须满足 v3。

## 3. Actions Governor

Governor 每 10 分钟扫描仓库真实的 `in_progress` 与 `queued` 运行。

### 3.1 重复运行

普通任务按 `workflow + branch + event` 去重，只保留最新一条。被更新 Commit 替代的旧任务直接取消，不恢复旧 Commit，因为最新运行本身已经是重新提交。

### 3.2 异常长运行

- 普通任务：45 分钟硬上限；
- Release / Deploy / Publish / Store Package：180 分钟；
- Strategy 内部任务：20 分钟。

### 3.3 历史任务

Governor 查询当前仓库状态，所以策略上线之前已经启动的异常任务也能被识别。

对于真正 stale/historical 的任务，v3 **禁止只 Cancel 后结束**：Cancel 释放 Runner 以后必须 dispatch `Actions Recovery`。

## 4. Actions Recovery：自动修复 + 重新提交

部署 `.github/workflows/actions-recovery.yml` 与 `.github/scripts/actions_strategy_autofix.py`。

Recovery 流程：

1. 读取源 run metadata 和日志。
2. 从当前默认分支加载最新版 v3 修复逻辑，因此可处理旧 Commit。
3. 自动修复安全、机械可确定的 Workflow 问题：
   - 缺少 `workflow_dispatch`；
   - 缺少 `permissions`；
   - 缺少 `concurrency`；
   - Job 缺少 `timeout-minutes`。
4. 如果仓库提供 `.github/actions-recovery.sh`，执行项目级确定性修复。该 hook 应为幂等规则，并可读取 `ACTIONS_RECOVERY_LOG`。
5. 有修改时创建 `actions-recovery/run-<run_id>` 分支并提交 Recovery PR。
6. 对普通无副作用 Workflow，显式 dispatch 修复后的 ref，完成重新提交。
7. 如果没有安全修改，允许最多一次 fresh-run rerun，用于 Runner / 网络 / 临时环境故障。
8. 自动恢复预算耗尽时创建 `[Actions Recovery]` Issue，不允许无限重跑。

## 5. “自动修复”的安全定义

Strategy v3 不假装能凭空推断任意业务代码的正确实现。自动修复分两层：

### 通用修复层

由 `actions_strategy_autofix.py` 处理所有可机械确定的 GitHub Actions 配置缺陷。

### 项目修复层

由 `.github/actions-recovery.sh` 编码项目已经确认过的故障模式。例如某类 fixture、生成文件、缓存状态、锁文件或配置迁移问题，只要能写成幂等规则，就可以自动修改并重新提交。

如果故障属于全新的业务逻辑错误、且没有确定性修复规则，v3 会停止自动猜测并建立 Recovery Incident。

## 6. 发布类安全边界

Release / Deploy / Publish / Store Package 可能对外部系统产生不可逆副作用，禁止盲目自动重放。

v3 可以：

- 自动修复其 Workflow 策略问题；
- 创建修复 PR；
- 建立 Recovery Incident。

但正式发布/部署的再次执行需要明确批准，避免重复 Release、重复部署或重复上传。

## 7. 老项目标准恢复链路

```text
历史卡死 run
    ↓
Governor 判定 stale
    ↓
Cancel 释放资源
    ↓
Actions Recovery 自动取证
    ↓
通用修复 + 项目 hook
    ↓
Recovery branch / PR
    ↓
普通 Workflow 显式 redispatch
    ↓
若无修改 → fresh-run rerun 1 次
    ↓
仍失败 → Recovery Issue
```

## 8. 新项目接入

至少复制：

1. `templates/ci.yml`
2. `templates/actions-governor.yml`
3. `templates/actions-recovery.yml`
4. `templates/actions-policy-check.yml`
5. `scripts/actions_strategy_autofix.py` → `.github/scripts/actions_strategy_autofix.py`
6. `scripts/validate_actions_strategy.py` → `.github/scripts/validate_actions_strategy.py`

有已知可确定修复模式时，再新增 `.github/actions-recovery.sh`。

## 9. 验收标准

只有同时满足以下条件才算 v3 落地：

- 同一 PR 连续 push，旧普通 CI 自动取消；
- 新增/修改 Workflow 必须通过 Policy Check；
- 普通任务不存在无限 `in_progress`；
- 历史 stale run 被取消后能看到 Recovery 接管；
- 可安全修复的问题会产生 repair branch/PR；
- 修复后的普通 Workflow 会重新 dispatch；
- 没有修复内容时只允许一次 fresh rerun；
- 自动恢复达到安全边界后会生成 Recovery Issue；
- 发布类不会被自动盲目重放。
