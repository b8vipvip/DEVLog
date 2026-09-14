# Solutions 索引

这里用于长期归档开发过程中遇到的问题、根因分析、修复方法和可复用模板。

## 已归档

- [`github-actions-standard-template/`](./github-actions-standard-template/)：GitHub Actions 标准模板。重点解决重复 CI、旧 PR 任务不取消、测试无限等待、临时 Debug Workflow 泛滥、重型任务误触发、Release 并发冲突等问题。

## 后续新增建议

每个问题使用独立目录，例如：

```text
solutions/
├── github-actions-standard-template/
├── nginx-502-troubleshooting/
├── python-dependency-conflict/
└── windows-service-recovery/
```

每个目录尽量包含：

1. 问题现象
2. 影响范围
3. 根因
4. 排查过程
5. 最终解决方案
6. 可复用脚本/配置
7. 预防措施
