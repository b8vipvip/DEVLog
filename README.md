# DEVLog

用于沉淀开发过程中可复用的问题排查、工程规则、自动化策略与解决方案。

## GitHub Agent v4

[`github-agent/`](./github-agent/) 是当前 GitHub Actions 标准：PR-aware concurrency、Fast Gate -> Full Gate、path-aware heavy builds、Governor ghost force-cancel、失败分类、Single Release Authority 与 Node24-native action baseline。

四个高频项目的审计和整改顺序见 [`github-agent/AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md`](./github-agent/AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md)。

后续遇到可复用的工程问题继续沉淀到对应目录，优先形成可执行模板、检查脚本和验收规则，而不是只记录文字结论。
