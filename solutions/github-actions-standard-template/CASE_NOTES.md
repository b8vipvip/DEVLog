# 案例记录：GPTWork 与 chat2api

这套规范来自两个真实项目中遇到的 GitHub Actions 问题。

## GPTWork

现象：

- Actions 历史运行很多，页面看起来非常复杂；
- 失败看似越来越频繁；
- 实际检查后发现，问题并不是“历史运行次数太多导致 GitHub 降速”。

经验：

- 历史 workflow run 数量本身不会直接降低编译成功率；
- 要优先检查当前一次提交到底触发了哪些 Workflow、哪个 Job、哪个 Step 变慢或失败；
- 不要仅凭 Actions 页面历史记录数量判断 GitHub Runner 被“用慢了”。

## chat2api

现象：

- 同一个 PR 连续提交后，CI #1735、#1736、#1737 同时处于运行中；
- 多条旧 CI 没有自动取消；
- pytest 长时间停留在 `in_progress`。

根因一：CI 缺少 concurrency。

因此每次 `pull_request synchronize` 都会启动新 CI，而旧 CI 继续运行。

标准修复：

```yaml
concurrency:
  group: ci-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

根因二：测试 fixture 与新的生产语义不一致。

项目新逻辑要求 Worker 不仅 transport online，还必须 ChatGPT 登录并 composer ready 后才能参与路由；旧测试只注册 Worker，却继续等待 `chat.request`，最终 WebSocket `receive_json()` 永久等待。

经验：

- 状态机、权限、登录条件、路由条件变化时，必须同步检查所有测试 fixture；
- WebSocket receive、Future、thread、process、HTTP 等等待必须设置 timeout；
- CI Job 也必须设置 `timeout-minutes`，形成双层保护。

根因三：临时 Debug Workflow 自动绑定 feature 分支 push。

每修一次测试又额外触发一次 Debug Workflow，导致 Actions 页面不断增加 3 分钟左右的失败任务。

标准修复：

```yaml
on:
  workflow_dispatch:
```

临时调试完成后应删除，或永久保留为手动触发。

## 最终结论

遇到 Actions “越来越慢 / 越来越容易失败”时，排查顺序应固定为：

```text
Workflow
  ↓
Job
  ↓
Step
  ↓
具体测试 / 命令
  ↓
是否存在等待、超时、状态 fixture 或并发问题
```

不要先通过增加 Runner、反复 Re-run 或连续提交多个小补丁来碰运气。
