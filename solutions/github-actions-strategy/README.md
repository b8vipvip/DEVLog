# GitHub Actions 策略 v3

这是统一的 GitHub Actions 治理方案，核心不是一份静态模板，而是 **Workflow Guard + Policy Check + Governor + Recovery + 项目修复 Hook**。

## 目录

- [`GITHUB_ACTIONS_STRATEGY.md`](./GITHUB_ACTIONS_STRATEGY.md)：v3 完整策略、恢复边界与验收标准。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目历史异常任务恢复 SOP。
- [`templates/ci.yml`](./templates/ci.yml)：普通 CI 基线。
- [`templates/actions-governor.yml`](./templates/actions-governor.yml)：重复/超时/历史异常任务治理。
- [`templates/actions-recovery.yml`](./templates/actions-recovery.yml)：异常任务自动取证、修复、Recovery PR 与重新提交。
- [`templates/actions-policy-check.yml`](./templates/actions-policy-check.yml)：新增/修改 Workflow 强制策略检查。
- [`templates/debug.yml`](./templates/debug.yml)：仅手动触发的 Debug 模板。
- [`templates/release.yml`](./templates/release.yml)：发布类串行模板。
- [`scripts/actions_strategy_autofix.py`](./scripts/actions_strategy_autofix.py)：通用安全自动修复器。
- [`scripts/validate_actions_strategy.py`](./scripts/validate_actions_strategy.py)：策略校验器。

## v3 与 v2 的主要区别

v2 的历史异常处理主要是 Cancel；v3 要求真正 stale 的任务在释放 Runner 后继续进入 Recovery：

```text
Cancel
  ↓
自动取证
  ↓
安全修复
  ↓
Recovery branch / PR
  ↓
普通任务重新 dispatch
  ↓
无安全修复时最多 fresh rerun 1 次
  ↓
仍不能恢复则创建 Recovery Issue
```

被更新 Commit 替代的 duplicate 例外：新一代运行本身就是重新提交，因此只取消旧任务，不复活旧代码。

## 默认阈值

- 普通 CI / Test / Smoke：45 分钟仓库级硬上限。
- Release / Deploy / Publish / Store Package：180 分钟。
- Strategy 内部 Workflow：20 分钟。
- Governor 自身 Job：10 分钟。
- Recovery Job：20 分钟。
- 无修改 fresh-run 自动重试：最多 1 次。

## 自动修复范围

通用层会修复可机械确定的 Workflow 问题，例如 concurrency、timeout、permissions、workflow_dispatch。

项目可以提供 `.github/actions-recovery.sh`，把已经确认的项目级故障模式编码成幂等自动修复规则。全新的业务逻辑错误不会被系统盲目猜测修改；达到安全边界后会生成 Recovery Issue。

## 当前已落地项目

- `b8vipvip/chat2api`
- `b8vipvip/GPTWork`

两个项目都要求后续 GitHub Actions 遵循 Strategy v3。
