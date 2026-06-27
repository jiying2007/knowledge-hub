# Knowledge Hub 终态硬切换会话归档

- Captured at: 2026-06-27 23:07:44 Asia/Hong_Kong
- Source scope: 当前 Codex 会话、`~/knowledge-hub`
- Project: knowledge-hub
- Workstream: final-hardcut-governance
- Commit: `36a706c chore(governance): 落地知识库终态硬切换`
- Sanitization: 未包含 secrets、完整聊天记录、私有 token、原始 session JSONL、运行态缓存或外部源正文
- Memory action: candidate

## 本次完成

### 终态硬切换

- 将 `~/knowledge-hub` 固化为唯一知识控制面。
- 新增 `tools/knowledge-context.sh`，用于跨项目、跨会话按 `cwd`、`query`、`task-type` 解析 Hub 路由、候选知识和归档落点。
- 新增项目/仓库/组件/工作区 registry：
  - `registry/project-routes.json`
  - `registry/repositories.json`
  - `registry/project-groups.json`
  - `registry/components.json`
  - `registry/workspaces.example.json`
- 新增多个 `projects/<project>/README.md`，固定项目知识入口。

### 去残留与防漂移

- 确认 `projects/` 下没有 `archive/source-docs` 残留。
- `runtime-rules` 路径审计旧路径命中为 0。
- 旧 `~/embedded/engineering_archive`、`~/codex/docs/archive` 只允许作为 canonical policy 或 provenance，不再作为当前运行入口。
- `~/knowledge-hub`、`~/codex`、`~/.codex` 作为本机允许长期根；其他本机源码路径通过逻辑 workspace 表达，不写成长期事实。

### Review Queue 收口

- 清空 4 条 AI-human review queue：
  - `knowledge-hub-project-routes-20260626`
  - `knowledge-hub-context-tool-20260626`
  - `knowledge-hub-git-remote-route-registry-20260626`
  - `pcr02-core-sensor-in0-935-1782474660-gdb-session-20260626`
- 本轮只做普通受托复核记录：
  - 不生成 owner decision。
  - 不关闭 owner gate。
  - 不提升 active。
  - 不写 memory。
  - 不改源项目。
- `pcr02-core-sensor_in0` 条目仅确认中断调试归档可检索，不确认根因结论。

## 关键决策

- 终态不兼容旧入口；旧路径只保留历史 provenance 语义。
- 项目入口固定为 `projects/<project>/README.md`。
- 项目界定优先按 Git remote / repository / component registry，而不是按本机绝对路径。
- `knowledge-context.sh` 是后续 Codex 会话进入 Hub 的默认上下文预检入口。
- review queue 的普通 AI-human review 可以按用户授权受托回填复核记录，但不得冒充 owner approval。

## 验证情况

- `rtk bash tools/knowledge-final-gate.sh --json --final-profile max-body`: pass，`final_status=ok`，`blockers=[]`，`gap_map=[]`
- `rtk bash tools/knowledge-final-gate.sh --json`: pass，`final_status=ok`
- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`: pass，`errors=[]`，`warnings=[]`
- `rtk bash tools/knowledge-path-audit.sh --scope runtime-rules --strict --json`: pass，`match_count=0`
- `rtk git diff --cached --check`: pass
- 提交后 `git status --short`: clean

## 经验与风险

- `knowledge-final-gate --final-profile max-body` 会把普通 AI-human review queue 也作为终态 blocker；标准 final gate 可通过不代表严格终态已清零。
- 旧 gate 输出可能来自修改前启动的长跑进程；修复后必须重新启动 gate，以最新结果为准。
- `commit-ready` 可能报告 `~/codex` 资产仓风险；判断 `knowledge-hub` 是否闭环时，应以本仓 `knowledge-check`、`knowledge-regression`、`knowledge-final-gate` 和 path audit 为准。
- session、memory、historical archive 中的旧路径文本不等于当前运行入口；应通过 `runtime-rules` scope 判定是否会影响新会话。

## 下一步

- 后续涉及归档路径、项目入口、debug/release/decision/source 任务时，先运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "<任务或问题>" --task-type <type> --json
```

- 若其他会话仍输出旧 `~/embedded/engineering_archive` 或 `~/codex/docs/archive`，先检查是否命中 runtime rules；不要根据历史 session 文本直接判定当前规则漂移。
- 若需要把本轮经验写入长期 memory，应先审查 memory candidate，不直接写 `~/.codex/memories`。
