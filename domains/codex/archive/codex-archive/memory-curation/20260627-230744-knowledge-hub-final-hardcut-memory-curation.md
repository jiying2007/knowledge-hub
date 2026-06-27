# Knowledge Hub 终态硬切换记忆整理报告

- Captured at: 2026-06-27 23:07:44 Asia/Hong_Kong
- Source scope: 当前 Codex 会话、`~/knowledge-hub@36a706c`
- Sanitization: 未包含 secrets、完整聊天记录、私有 token、原始 session JSONL、运行态缓存或外部源正文
- Mode: report-only with memory candidates
- Long-term memory writes performed: 0

## Source Counts

- Repository reviewed: 1
  - `~/knowledge-hub`
- Commit referenced: 1
  - `36a706c chore(governance): 落地知识库终态硬切换`
- Gates referenced: 5
  - `knowledge-check`
  - `knowledge-final-gate`
  - `knowledge-final-gate --final-profile max-body`
  - `knowledge-path-audit --scope runtime-rules --strict`
  - `git diff --check`

## High Signal Findings

- `~/knowledge-hub` 已具备标准终态和严格终态两条完成线；严格终态需要 review queue 清零。
- 跨会话使用 Hub 的关键入口是 `tools/knowledge-context.sh`，而不是记忆里的旧路径或项目 README 的零散提示。
- 项目边界应由 Git remote、repository registry、component registry 和 project route 共同表达；本机绝对路径只能作为 workspace 示例或本地私有映射。
- 旧路径残留要分层判断：current runtime route 命中必须修；canonical policy、provenance、historical session 默认可保留。
- 普通 AI-human review 受托回填不等于 owner decision，也不允许提升 active 或关闭 owner gate。

## Duplicate/Stale Findings

- 旧 `~/embedded/engineering_archive`、`~/codex/docs/archive` 已被 Hub hard-cut 废止；若未来 memory 或历史 session 提到这些路径，只能当 retired provenance。
- `commit-ready` 针对 `~/codex` 的 THREAD_LONG、asset changed 等提示不应混同为 `knowledge-hub` 本仓门禁失败。
- `pcr02-core-sensor_in0` GDB 会话归档是中断调试记录，不能被提升为根因结论。

## Memory Candidates

| Scope | Candidate | Evidence | Risk | Confidence | Write Route |
|---|---|---|---|---|---|
| knowledge-hub route | 归档路径、项目入口、debug/release/decision/source 问题应先跑 `knowledge-context.sh`，再回答或落盘。 | `tools/knowledge-context.sh` 已提交；standard/max-body final gate 均通过。 | low | high | memory candidate -> project rule / AGENTS candidate |
| knowledge-hub final gate | 判断 Hub 是否到终态时，标准 gate 和 max-body gate 要区分；max-body 还要求 AI/外部资料 review queue 清零。 | 本轮先出现 4 条 review queue blocker，受托复核后 max-body `final_status=ok`。 | low | high | memory candidate -> project rule |
| path hardcut | 旧 `~/embedded/engineering_archive`、`~/codex/docs/archive` 只可作为 provenance；是否影响新会话以 `knowledge-path-audit --scope runtime-rules --strict` 为准。 | runtime-rules 审计 `match_count=0`，Hub 内旧路径只剩 canonical/provenance 分类。 | medium | high | memory candidate -> global preference / project rule |
| review queue boundary | AI-human review 受托回填只能记录普通复核，不生成 owner decision、不关闭 owner gate、不提升 active、不写 memory。 | 4 条 review queue 已清零，registry 中保留 `promotion_decision=none`。 | medium | high | memory candidate -> governance rule |
| interrupted debug archive | 中断调试归档只证明会话可检索和状态可恢复，不证明技术根因。 | `pcr02-core-sensor-in0-935-1782474660-gdb-session-20260626` review basis 明确未确认根因。 | low | medium | archive-only or project memory candidate |

## Archive-only Items

- 本轮完整 gate JSON、长 review queue 输出和路径扫描原始输出只保留为过程证据，不写入长期 memory。
- 49 个文件的提交统计适合作为归档证据，不需要提升为长期记忆。
- 具体项目 README 列表和 registry 行级内容由 Git 提交保存，不重复写入 memory。

## Drop/Review Items

- 不保存完整聊天记录。
- 不保存 `.codex/sessions`、cache、raw runtime output。
- 不把一次性提交前状态、旧 gate 过期输出、临时 session id 输出写入长期 memory。
- 若后续要写 `~/.codex/memories`，需人工确认候选、脱敏、回滚路径和冲突检查。

## Gate Result

pass: 已生成可审查记忆候选和会话归档；未直接写入长期 memory。
