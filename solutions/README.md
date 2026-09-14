# Solutions 索引

这里用于长期归档开发过程中遇到的问题、根因分析、修复方法和可复用策略。

## 已归档

- [`github-agent/`](./github-agent/)：**GitHub Agent**。原“GitHub Actions 策略”已正式更名。重点解决重复 CI、旧 PR 任务不取消、测试无限等待、历史异常任务持续占用资源、临时 Debug Workflow 泛滥、重型任务误触发、Release 并发冲突，并提供 Recovery、确定性自动修复、Recovery PR 和可选 coding-agent 智能修复委派。
- [`github-actions-strategy/`](./github-actions-strategy/)：旧名称兼容目录，暂时保留以避免历史链接失效。

## 后续新增建议

每个问题使用独立目录，例如：

```text
solutions/
├── github-agent/
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
