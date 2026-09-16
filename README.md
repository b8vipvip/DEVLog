# DEVLog

用于沉淀开发过程中可复用的问题排查、工程规则、自动化策略与解决方案。

## 当前核心方案

- [`github-agent/`](./github-agent/) — **GitHub Agent v4**：面向高频开发仓库的 GitHub Actions 治理与恢复标准。
  - PR-aware concurrency：PR 淘汰旧 SHA，默认分支正式验证允许完成。
  - Fast Gate -> Full Gate 与 path-aware heavy builds。
  - Governor v4：normal cancel -> recheck -> force-cancel，清理 jobless ghost runs。
  - 失败分类：deterministic / workflow config / infra transient / ghost / superseded / side-effectful。
  - Single Release Authority 与 Node24-native action baseline。
- [`github-agent/AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md`](./github-agent/AUDIT_2026-09-16_HIGH_FREQUENCY_REPOS.md) — chat2api、GPTWork、fdex、qnbot 深度审计与整改顺序。

后续遇到可复用的工程问题与解决方案继续沉淀到对应目录，优先形成可执行模板、检查脚本和验收规则，而不是只记录文字结论。
