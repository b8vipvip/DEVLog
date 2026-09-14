# GitHub Actions 标准规范

这套模板用于所有新项目，目标是避免：

- 同一 PR 连续提交后，多条旧 CI 同时运行；
- pytest / npm / WebSocket / 浏览器测试无限等待；
- 临时 debug / one-shot Workflow 长期污染 Actions；
- 重型 Docker / E2E 在无关改动时重复执行；
- Release / Tag / Artifact 被多条流水线同时修改。

## 必须遵守的规则

1. **PR CI 必须有 concurrency**
   - 同一个 PR 只保留最新一次运行。
   - `cancel-in-progress: true` 只用于 PR / 可安全取消的验证。

2. **main / Release 不要随意强制取消**
   - 正式 CI 可以完整跑完。
   - Release 使用固定 concurrency group 串行化。
   - Release 默认 `cancel-in-progress: false`。

3. **每个 Job 必须设置 timeout-minutes**
   - 普通 CI：10–20 分钟。
   - Docker / E2E：20–40 分钟。
   - Debug：5–10 分钟。

4. **容易阻塞的命令必须有内部 timeout**
   - pytest
   - npm test
   - Playwright / Selenium
   - WebSocket receive
   - process.wait / thread.join / event.wait / future.result
   - 外部 HTTP 请求

5. **feature 分支通常只使用 pull_request**
   - 不要同时给 feature/fix 分支配置 `push` + `pull_request` 两套相同 CI。
   - `push` 通常只保留 `main`。

6. **临时 Debug Workflow 只能 workflow_dispatch**
   - 调试完删除。
   - 禁止长期 `on: push: branches: [fix/xxx]`。

7. **重型 Workflow 必须使用 paths**
   - README、文档等无关变化不应触发 Docker / E2E。

8. **生产语义变化时同步更新测试 fixture**
   - 登录状态、权限、路由条件、状态机发生变化时，必须搜索所有旧 fixture。
   - 防止“测试一直等待一个新逻辑永远不会发出的事件”。

9. **Release 与 CI 分离**
   - PR 验证不能修改 Tag / Release。
   - 同一时间只允许一个 Release 流程触碰生产发布资源。

10. **不要用连续几十个提交试到 CI 变绿**
    - 先定位：Workflow → Job → Step → Test。
    - 找到第一个确定故障后再修改。

## 推荐长期保留的 Workflow

```text
.github/workflows/
├── ci.yml
├── production-smoke.yml
├── release.yml
└── debug.yml            # 可选，且必须手动触发
```

不建议长期保留：

```text
one-shot-*.yml
tmp-*.yml
debug-branch-*.yml
fix-once-*.yml
finalize-temp-*.yml
```

## PR CI 标准并发规则

```yaml
concurrency:
  group: ci-${{ github.event.pull_request.number || github.sha }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}
```

## Release 标准并发规则

```yaml
concurrency:
  group: production-release
  cancel-in-progress: false
```

## 合并前检查清单

- [ ] 同一个 PR 连续 push 时，旧 CI 会自动 cancelled。
- [ ] Job 有 `timeout-minutes`。
- [ ] 测试内部没有无限等待。
- [ ] Debug Workflow 不是 push 自动触发。
- [ ] Docker / E2E 有合理的 `paths`。
- [ ] PR Workflow 不会修改 Tag / Release。
- [ ] Release 串行执行。
- [ ] Branch protection 只要求长期稳定的正式检查。
- [ ] 临时 Workflow 已删除或改成手动。
- [ ] 生产状态机改变后，旧测试 fixture 已同步更新。
