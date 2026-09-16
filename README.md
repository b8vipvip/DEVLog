# DEVLog

用于沉淀开发过程中可复用的问题排查、工程规则、自动化策略与解决方案。

## GitHub Agent v4

[`github-agent/`](./github-agent/) 是当前 GitHub Actions 标准：PR-aware concurrency、Fast Gate -> Full Gate、path-aware heavy builds、Governor ghost handling、失败分类、Single Release Authority 与 Node24-native action baseline。

其中 `GITHUB_PLATFORM_GHOST` 专门表示 GitHub 对长期 active/no-job run 连普通 cancel 与 force-cancel 都拒绝的异常状态；这类 run 隔离记录，不计入代码失败率。

四个高频项目的审计和整改进度见 [`github-agent/AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md`](./github-agent/AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md)。
