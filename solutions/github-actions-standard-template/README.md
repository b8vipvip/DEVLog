# GitHub Actions 标准模板

这是 DEVLog 中的 GitHub Actions 通用规范与模板，整理自实际项目中遇到的 CI 重复运行、测试卡死、临时 Workflow 泛滥等问题。

## 适用目标

这套模板主要用于避免：

- 同一 PR 连续提交后，多条旧 CI 同时运行；
- pytest / npm / WebSocket / 浏览器测试无限等待；
- 临时 debug / one-shot Workflow 长期污染 Actions；
- Docker / E2E 等重型任务在无关改动时重复执行；
- Release / Tag / Artifact 被多条流水线同时修改；
- 通过连续提交大量小补丁“试到 CI 变绿”。

## 目录

```text
github-actions-standard-template/
├── README.md
├── GITHUB_ACTIONS_STANDARD.md
├── CASE_NOTES.md
└── templates/
    ├── ci.yml
    ├── production-smoke.yml
    ├── release.yml
    └── debug.yml
```

## 使用方法

将 `templates/` 中需要的文件复制到目标项目根目录的：

```text
.github/workflows/
```

通常建议：

```text
.github/workflows/
├── ci.yml
├── production-smoke.yml
├── release.yml
└── debug.yml            # 可选，只能手动触发
```

然后按目标项目实际情况修改 Python/Node 版本、依赖安装方式、Docker 端口、健康检查和正式发布命令。

## 新项目推荐步骤

1. 先启用 `ci.yml`。
2. 有 Docker / E2E 后再启用 `production-smoke.yml`。
3. 准备正式发布时再补全 `release.yml`。
4. `debug.yml` 仅用于临时排障，保持 `workflow_dispatch` 手动触发。
5. Branch protection / Rulesets 只要求长期稳定的正式检查，不要依赖临时 Debug Workflow。

## 第一次适配必须检查

- 默认分支是否为 `main`；不是则修改触发分支。
- Python / Node 版本是否符合项目。
- Python 使用 `requirements.txt`、`pyproject.toml` 还是其它方式安装。
- Node 使用 npm、pnpm 还是 yarn。
- pytest / npm test 是否存在网络、WebSocket、浏览器、线程、进程等待；这些必须有明确 timeout。
- Docker 服务端口和 health endpoint。
- Release 的打包命令、产物路径和发布方式。

## 核心原则

> CI 的目标不是“什么都跑”，而是：**尽快失败、明确失败、只验证最新代码、绝不无限等待。**
