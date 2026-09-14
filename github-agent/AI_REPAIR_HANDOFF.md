# AI Repair Brief 交接规范

当 GitHub Agent 无法通过确定性规则安全修复问题时，不接入任何 coding-agent provider，而是生成标准化 Issue，把问题交给用户选择的 AI。

## Issue 标题

```text
[GitHub Agent][AI Repair] <workflow> run <run_id>
```

## 必填内容

1. Repository、Source Run、Workflow、Workflow path。
2. Branch、Commit SHA、Event、Run attempt。
3. Governor / Recovery reason。
4. Failed jobs / failed steps。
5. 高信号错误行摘要，并明确要求 AI 阅读完整日志。
6. Deterministic repair 是否产生、Repair PR 地址。
7. 是否属于 Release / Deploy / Publish / Store Package。
8. 是否命中瞬时基础设施故障特征、是否已做一次受限 rerun。
9. AI 修复任务说明。
10. 验收标准。

## 给 AI 的标准任务

接手 AI 必须：

- 读取 Issue、完整 Source Run、对应 Commit 和相关代码；
- 先检查源 Commit 是否已被新的修复替代；
- 分析根因，不以“让测试绿”为唯一目标；
- 在独立修复分支修改代码；
- 默认禁止直接写 `main`；
- 运行原失败测试、相关回归测试和 GitHub Agent Policy Check；
- 建立或更新 PR，并说明根因、改动、验证证据和剩余风险；
- 禁止自动盲目重放 Release / Deploy / Publish / Store Package。

## 日志摘要原则

Issue 只放定位所需的高信号错误摘要，不复制完整日志。完整日志通过 Source Run 链接读取，避免 Issue 过大，也降低把无关运行数据复制到 Issue 的风险。

建议提取关键词包括：

```text
error
failed
failure
traceback
assert
exception
timeout
timed out
fatal
hang
cancelled
ECONNRESET
ETIMEDOUT
ENOTFOUND
502 / 503 / 504
```

## 瞬时故障处理

仅在日志明确符合 Runner / 网络 / DNS / 网关等瞬时故障特征时允许一次 fresh rerun。即使已触发 rerun，只要没有产生确定性代码修复，仍然建立 AI Repair Brief，保证问题有可追踪交接记录。

## 目标

GitHub Agent 不负责替代用户选择的 AI。它负责把“发生了什么、失败在哪里、已经尝试过什么、修复时有哪些边界、怎样才算修好”整理完整，让 AI 接手后能够直接进入排查与修复，而不必从零重新收集上下文。
