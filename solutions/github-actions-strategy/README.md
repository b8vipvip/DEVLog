# GitHub Actions 策略

这是统一的 GitHub Actions 治理策略，适用于：

- 新项目首次接入 Actions；
- 已经存在大量 Workflow 的老项目；
- 同一 PR 多次 push 后产生大量并发 CI；
- pytest / npm / cargo / Docker 构建卡死，Actions 长时间保持 `in_progress`；
- 历史异常任务仍在占用 Runner 或排队资源；
- 临时 Debug Workflow 越积越多；
- Release / Deploy 与普通 CI 之间互相干扰。

本目录不再使用“标准模板”这个名称。核心思想是 **策略 + 强制治理 + 老项目恢复 + 可复用模板**。

## 目录

- [`GITHUB_ACTIONS_STRATEGY.md`](./GITHUB_ACTIONS_STRATEGY.md)：完整策略与验收标准。
- [`LEGACY_PROJECT_RECOVERY.md`](./LEGACY_PROJECT_RECOVERY.md)：老项目迁移、历史异常任务清理与恢复 SOP。
- [`templates/actions-governor.yml`](./templates/actions-governor.yml)：仓库级 Actions Governor，自动清理重复与超时运行。
- [`templates/ci.yml`](./templates/ci.yml)：普通 CI 基线模板。
- [`templates/debug.yml`](./templates/debug.yml)：仅手动触发的临时诊断模板。
- [`templates/release.yml`](./templates/release.yml)：发布类串行模板。

## 当前默认阈值

- 普通 CI / Test / Smoke：仓库级 45 分钟硬上限。
- Release / Deploy / Publish / Store Package：仓库级 180 分钟硬上限。
- Actions Governor：每 10 分钟执行一次，自身 Job 最长 10 分钟。
- 同一普通 workflow + branch + event：只允许最新一条继续运行。

## 当前已落地项目

- `b8vipvip/chat2api`
- `b8vipvip/GPTWork`

两个项目均要求后续 GitHub Actions 运行遵循本策略，并使用仓库级 Actions Governor 作为老任务与异常长运行的兜底治理层。
