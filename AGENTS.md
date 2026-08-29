# Knowledge Hub Agent Rules

Knowledge Hub（`~/knowledge-hub`）是团队、项目、Codex 与个人知识的统一控制面。本文件只保留每轮硬边界；字段、命名、证据、中文可读性和工具规则以 `registry/schema.md`、`governance/`、`templates/` 为准。

## 1. 分类与权威

- 先分类、后落盘；先 registry、后提升。正文只维护一份，其他位置使用索引、引用或迁移记录。
- 权威位置：
  - 团队已发布规范/runbook：`workspace://embedded-knowledge`
  - 嵌入式候选、提炼稿与历史 provenance：`domains/embedded/`
  - 项目当前事实、决策、历史：`projects/<project>/current|decisions|archive/`
  - 专利：`domains/patents/`；Codex 治理：`domains/codex/`
  - 个人草稿：`notes/personal/`，不得进入团队 active index
- Hub 当前事实高于 memory、raw session 和旧 archive provenance；摘要冲突时回读原文与可复跑证据。
- 长期文本默认简体中文并保留必要技术标识；复用 `templates/`，结论、证据、风险和下一步分开写。

## 2. 权限与生命周期

- 本仓内 Markdown、registry、index、manifest、template、tooling 的 L1/L2 维护、整理和门禁属于可审计本地维护；不得据此扩大到源项目或运行时。
- 自动化默认 `report-only`。删除、发布、push/merge/rebase/tag、提升 active、owner decision、关闭 owner gate、写 memory、修改源项目或外部系统，必须有明确授权、证据、回滚和验证。
- 不以本地 commit 代替 owner approval、promotion、source write、memory write 或远端发布授权；当前工作区上层规则禁止时不得自动 commit。
- reviewing candidate 不是 active 事实；来源、owner、状态、review 周期未验证前不得声明 active。AI 受托 owner 操作必须记录授权和执行身份。

## 3. 内容硬边界

- project-specific 内容不得直接进入团队发布库；跨项目提炼稿先进入 `domains/embedded/` reviewing，再经团队库提升契约、owner review 和全量门禁发布。`notes/personal/` 不进团队索引。
- 禁止写入 raw log、core、SDK 包、binary、token、private key、password、cookie、运行时 secret、客户/设备标识。
- 不复制完整会话或 owner-gated source 正文；候选必须脱敏、可复用、有 provenance 和 raw fallback。
- `~/.codex/memories` 仅辅助召回，不能是规则/事实唯一来源；无授权账本不得写入。

## 4. 查询、候选与工具资产

- 项目事实查询优先显式项目、small budget、summary：

```bash
rtk bash tools/knowledge-context.sh --cwd "$PWD" --project <project_id> --query "<任务>" --task-type <type> --context-budget small --limit 3 --summary-json --no-telemetry
```

仅路由歧义、解释不足或高风险结论回退 `--json` 与候选原文。只读预检默认不写 telemetry；需要运营统计时显式启用。
- debug/release/decision 产生耐久、可复用且有证据的结论时生成 reviewing candidate；validation/general 默认不强制。无合格结论应输出“本次无可归档结论”。
- 工具资产会话用 `tools/knowledge-capture.sh --tool-asset-session-start|--tool-asset-session-close`；baseline 只存 HEAD、路径、size、SHA256，不存 prompt、参数值或环境变量。
- 工具候选需同项目至少两个不同会话复用，或至少三个会话且覆盖两个项目；只生成 reviewing dry-run 计划。candidate 仅写项目 `tmp/`、`.tmp/` 或系统 `/tmp`，未经授权不用 `--apply`。

## 5. 验证

```bash
rtk bash tools/knowledge-check.sh --dry-run
rtk bash tools/knowledge-search.sh "PCR02 OTA"
```

修改 Codex 自动化/manifest 时还需在 `~/codex` 运行 governance、routing、check 与 final-ready 门禁。无新鲜证据不得声称完成。
