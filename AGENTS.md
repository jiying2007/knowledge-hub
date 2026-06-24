# Knowledge Hub Agent Rules

## 1. 基本定位

- 根目录：`~/knowledge-hub`
- 角色：统一知识控制面
- 范围：团队知识、项目事实、工程归档、专利材料、Codex 工作流、个人草稿和外部制品引用。

## 2. 工作原则

- 先分类，再落盘；先 registry，再提升。
- 正文只维护一份；其他位置使用索引、引用或迁移记录。
- Git 管理下的 Knowledge Hub 默认允许 AI / Codex 执行 L1/L2 维护：修改本仓内 Markdown、registry、index、manifest、template、tooling，移动或整理本仓内知识文件，运行门禁，并在门禁全绿后创建本地 commit。
- 本地 commit 是可审计、可回滚的 Hub 内维护动作，不等于发布；自动 push、merge、rebase、tag、release 或改远端状态仍属高风险动作。
- 自动化默认 `report-only`；删除、发布、push/merge、提升 active、生成或落地 owner decision、关闭 owner gate、写 memory、修改源项目等高风险动作，必须先有授权账本记录、证据、回滚路径和验证命令。
- `~/.codex/memories` 默认只作为辅助召回，不能作为规则或事实的唯一来源；只有授权账本允许时才可写入。
- 文档、资料、索引、manifest、worksheet 和其他文本类产物默认使用简体中文，必要的命令、路径、协议字段、API 名称、代码标识和英文原文引用可保留英文。
- 所有长期保留文本应优先保证可读性：标题清楚、段落短、列表有边界、结论/证据/风险/下一步分开写；外文或机器生成材料进入知识库时，应补中文摘要或中文说明，避免只留下难检索的原始文本。
- 中文开发人员长期资产规范以 `governance/chinese-readability.md`、`governance/glossary.md`、`governance/evidence-rules.md`、`governance/naming-boundaries.md` 和 `governance/ai-generated-content-labeling.md` 为准。
- 新增长期文档优先复用 `templates/`；命令证据、外部资料吸收、排障记录、owner review、commit/changelog/PR 分别遵守 `governance/command-tooling-rules.md`、`governance/external-source-absorption.md`、`governance/debug-record-rules.md`、`governance/owner-review-rules.md`、`governance/commit-changelog-pr-rules.md`。

## 3. 权威边界

- 团队级规范和跨项目 runbook：`domains/embedded/`
- 当前项目事实：`projects/<project>/current/`
- 项目历史证据：`projects/<project>/archive/`
- 当前有效项目决策：`projects/<project>/decisions/`
- 专利披露与检索：`domains/patents/`
- Codex 会话和工作流治理：`domains/codex/`
- 个人草稿和普通笔记：`notes/`

## 4. 禁止事项

- 禁止把 project-specific 内容提升到 `domains/embedded/standards/`。
- 禁止把 `notes/personal/` 内容加入团队 active index。
- 禁止把 raw logs、core、SDK 压缩包、release binary 写入文本知识层。
- 禁止把 token、private key、password、cookie 或运行时 secret 写入任何正文或 registry。
- 禁止在未验证来源、owner、状态和 review 周期前声明知识条目 active。
- 禁止在缺少授权账本记录时由 Codex 或自动化代签 owner decision、代填 `reviewed_by`，或把 owner-ready / landing-plan 产物当成已关闭 gate。已授权时必须标明 AI / Codex 受托执行，并记录授权、证据、回滚和验证结果。
- 禁止把本地 commit 当作 owner approval、active promotion、source project write、memory write 或 remote publish 的授权依据。

## 5. 最小验证

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "PCR02 OTA"
```

修改 Codex 自动化或 manifest 后，还必须在 `~/codex` 执行：

```bash
rtk bash scripts/doctor.sh --scope governance
rtk bash scripts/check-routing-precedence.sh
rtk bash scripts/check.sh
rtk bash scripts/final-ready.sh
```
