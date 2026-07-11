# Knowledge Hub

Knowledge Hub 是本机长期知识主库：负责统一登记、检索和治理跨领域知识、项目知识、工程归档、专利材料、Codex 历史、AI 自动化和个人笔记。

终态模型：

```text
Knowledge Hub = Obsidian-friendly Markdown Vault + 最小 registry 账本 + 高风险授权门禁
```

## 日常入口

普通维护优先使用 5 条短命令：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json --as-of 2026-07-11
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --owner <owner> --id <id> --path <path>
rtk bash ~/knowledge-hub/tools/knowledge-search.sh "<关键词>" --json
rtk bash ~/knowledge-hub/tools/knowledge-review-after.sh --as-of 2026-07-11 --window-days 30 --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

这 5 条分别覆盖健康概览、新增草稿、检索、复核排期和一致性门禁。短概览只用于首屏判断；正式收口仍以 `knowledge-final-gate.sh` 为 terminal gate。

跨项目会话、排障、发布、归档或决策类问题先做 Hub 上下文预检：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd "$PWD" --query "<任务或问题>" --task-type general --json
```

预检结果用于确定项目入口、当前事实目录、归档目录、决策目录和候选知识落点。Codex memory、raw session 和项目本地 README 只能辅助定位，不能覆盖 Hub 当前事实。
上下文预算可用 `--context-budget small|normal|deep` 控制；输出中的 `canonical_paths`、`context.current`、`context.recent`、`context.related`、`context.search_fallback` 和 `why_selected` 用于解释 AI 为什么选中这些材料，不代表条目已提升 active 或 owner 已签收。
在 `~/knowledge-hub` 内自举维护时，`repo_route` 表示当前 cwd 属于 Knowledge Hub 仓库，`route` 表示 query 目标；如果 query 明确命中 PCR02、agent-dev-kit 等项目别名，预检仍应路由到目标项目。检查 Hub 自身治理上下文可用：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-context.sh --cwd ~/knowledge-hub --query "增强 Knowledge Hub 自举体验" --task-type general --context-budget small --json
```

路径类问题优先看：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-path-audit.sh --scope hub --json
rtk bash ~/knowledge-hub/tools/knowledge-path-audit.sh --scope runtime-rules --strict --json
```

人读规则见 `governance/path-routing.md`。新增归档、会话总结和排障记录只写 Hub canonical 路径；旧 `~/embedded/engineering_archive`、`~/codex/docs/archive` 和源项目旧 `docs/` / `knowledge/` / `tools/` 只作历史 provenance。

状态和收口再使用：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json --as-of 2026-07-11
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
```

`knowledge-final-gate.sh --json` 默认使用 quick regression，适合日常收口和提交前快速证明。

需要检查“正文最大收口”终态时，使用 `max-body` profile：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile max-body --full-regression
```

`standard` profile 保持日常自动治理边界：普通 AI / 外部资料人工复核队列是 report-only，不阻断 final gate。`max-body` profile 用于正文最大收口：待人工复核队列、`needs-edits` / `defer` 复核结果，以及不安全的 `copy-body` source inventory 都是 blocker。它仍然不代签 owner decision、不提升 active、不写 memory、不修改源项目。
成熟态使用 `mature` profile：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile mature --full-regression
```

`mature` profile 在 `max-body` 基础上进一步阻断迁移态残留：`migrated-*` 条目、copy-first / migration 过程 manifest、copy-first 工具入口、已关闭迁移 source 留在当前 source 主列表，以及长期滞留的高比例 `reviewing`。成熟态只允许保留不可误用的封存审计摘要；封存材料不得参与默认 search、context 或 routing。
`--full-regression` 是终态证明和高风险脚本改动后的重门禁；日常查询和普通维护优先使用 search/context/check/status。

长期运营成熟态入口见 `governance/status/knowledge-hub-operational-maturity.md`。该状态页把日常、周度和 release gate 命令、搜索验收、review_after 运营节奏和剩余风险固定为可审查产物；2026-07 近期待复核批次已在 `artifacts/manifests/knowledge-hub-review-after-operation-plan-20260701.md` 中按运营周期刷新到 2026-10，完整交付闭环见 `artifacts/manifests/knowledge-hub-complete-delivery-closure-20260701.md`。该闭环只收口 Hub 内治理 review 和运营尾巴，不生成 owner decision、不关闭 owner gate、不提升 active、不写 memory、不修改源项目、不伪造外部实机证据。

## 目录边界

| 目录 | 用途 | 维护强度 |
|---|---|---|
| `inbox/` | 未分类输入、临时草稿、待处理材料 | L0，可短期停留 |
| `notes/` | 普通长期笔记、个人笔记、学习和研究记录 | L1，registry 可选 |
| `projects/<project>/` | 项目当前事实、决策、验证和历史归档 | L2，registry 必填 |
| `domains/` | 跨项目领域知识、专利、Codex 治理材料 | L2，registry 按复用风险决定 |
| `sources/` | source 人读边界、inventory、coverage 和 source policy | L2，和 current/retired source registry 对齐 |
| `registry/` | 机器账本：items、sources、projects、owners、`registry/authorizations.jsonl`、`registry/automation-runs.jsonl` | L2/L3 |
| `indexes/` | 可重建导航，不是事实权威 | 可由工具检查 |
| `artifacts/manifests/` | 高风险 source 处置、owner gate、自动化和终态证据包 | L3 |
| `templates/` | 人工维护模板 | 低频维护 |
| `governance/` | 中文治理规则和边界 | 低频维护 |
| `tools/` | 检查、检索、诊断和门禁工具 | 变更后跑 regression/final gate |

新增内容不得写入旧项目/个人入口：

```text
domains/projects/**
domains/personal/**
```

旧路径只允许出现在 Git 历史、历史 manifest 或明确标记的 provenance 字段中，不作为当前查询、恢复或新增入口。

## Source 处置口径

“终态落地”采用治理全覆盖，不等于复制所有正文。

- 每个来源、项目、历史会话和自动化链路必须登记、分类、索引和定责。
- `registry/sources.json` 只保留当前 source 主表；已关闭来源进入 `registry/retired-sources.jsonl`，仅作 provenance ledger。
- `registry/retired-process-ledger.jsonl` 只保留迁移过程账本、dry-run、applied、classification 和 source inventory 的封存线索；它不是当前知识入口，不参与默认新增、提升或 owner gate。
- 每个 current 或 retired source 必须有 Hub 内 `sources/<source_id>/README.md`、`inventory.jsonl`、`coverage.md`、`source-policy.md`。
- 安全、可读、长期有价值的 Markdown/text 可以落到 canonical 正文。
- raw log、binary、SDK、release artifact、源码包、raw session、history jsonl 默认只登记引用、摘要、hash 或 artifact-ref。
- current/retired source registry 中的 `path` 必须指向 Hub 内 `sources/<source_id>`；当前知识入口只使用 Hub 内路径，retired source 不作为默认新增入口。
- Codex archive 当前 canonical 目录是 `domains/codex/archive/codex-archive/`；新归档和新索引只写 Knowledge Hub 终态目录。
- PCR02 工程归档当前 canonical 目录是 `projects/pcr02/archive/engineering-archive/pcr02/`；PCR02 新归档、会话总结和排障材料只写 Knowledge Hub 终态目录。
- `~/.codex/history.jsonl`、`~/.codex/sessions/**`、`~/.codex/memories/**` 只作为运行态输入或辅助召回 provenance，不复制 raw 正文，不直接等于 active fact。
- 全局路径回答和跨仓协同以 `governance/path-routing.md` 为准；发现旧路径召回时先运行 `knowledge-path-audit.sh`，再按 Hub / Codex runtime / memories / historical session 分类处理。

## 权威边界

- 项目事实：`projects/<project>/current/`
- 项目决策：`projects/<project>/decisions/`
- 项目验证：`projects/<project>/validation/`
- 项目历史：`projects/<project>/archive/`
- 普通和个人笔记：`notes/`
- 跨项目嵌入式知识：`domains/embedded/`
- 专利材料：`domains/patents/`
- Codex 会话、工作流和记忆治理：`domains/codex/`
- Source 边界说明和迁移控制面：`sources/`

`registry/items.jsonl` 是长期资产权威账本；`indexes/` 是可重建导航；`artifacts/manifests/` 是高风险证据包。

## AI 自动化权限

在 Git 管理下，AI / Codex 默认可执行 L1/L2 Hub 内维护：

- 修改本仓内 Markdown、registry、index、manifest、template 和 tools。
- 移动、重命名、归并本仓内知识文件。
- 生成 source coverage、source policy、review queue、automation run record。
- 运行 `knowledge-check`、`knowledge-regression`、`knowledge-final-gate`。
- 门禁全绿后创建本地 commit。

本地 commit 只代表可审计快照，不代表发布、owner approval 或 active promotion。自动 push、merge、release、tag、删除外部资料、修改源项目、写 memory、关闭 owner gate、提升 active 或改变远端 Git 状态仍必须走授权账本。

AI / 外部资料人工复核的默认路径是先导出 JSONL 骨架，再由真实人工填写 `human_reviewed_by`、`human_reviewed_at`、`review_basis` 和 `review_decision`：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section review-queue --queue-forms-jsonl > artifacts/manifests/review-queue.local.jsonl
rtk bash ~/knowledge-hub/tools/knowledge-review-queue-apply.sh --forms artifacts/manifests/review-queue.local.jsonl --dry-run --json
rtk bash ~/knowledge-hub/tools/knowledge-review-queue-apply.sh --forms artifacts/manifests/review-queue.local.jsonl --apply --json
```

`knowledge-review-queue-apply.sh` 只机械落地已校验人工复核字段；表单中出现 owner gate、active promotion、memory write、source project write 等字段会被拒绝。`needs-edits` 和 `defer` 会保留为 `max-body` blocker，直到人工补正或改判。

## 高风险授权

AI / Codex 可以执行以下高风险动作，但必须先有授权账本记录：

- 代签或落地 owner decision。
- 提升条目为 `active`。
- 写入 `~/.codex/memories` 或其他长期记忆层。
- 修改 PCR02 或其他源项目文件。
- 执行非 `report-only` 自动化，例如 `apply-with-review`。
- push、merge、release、tag 或其他远端 Git 状态变更。

授权记录写入 `registry/authorizations.jsonl`，必须包含：

- `authorization_id`
- `authorized_by`
- `authorized_at`
- `scope`
- `allowed_actions`
- `expires_at`
- `evidence_refs`
- `rollback_path`
- `validation_commands`

跨项目、跨会话自动化运行写入 `registry/automation-runs.jsonl`。没有授权记录时，AI / Codex 只能在 Hub 内执行 L1/L2 维护、本地 commit，或输出 plan、diff、manifest、review package、report-only 报告。

## 离线人工维护

无法立刻联网、上板、跑完整工具或确认 owner 时，可以先登记人工待验证状态，但不能把它当作已验证事实。

最小字段：

```yaml
source:
  type: manual
  from: field-debug / meeting / code-review / lab-test / owner-decision / design-review
status: reviewing
review_status: manual-entry-pending-review
manual_validation_pending: true
required_followup: rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

等价 JSON 片段：

```json
{
  "source": {
    "type": "manual",
    "from": "field-debug / meeting / code-review / lab-test / owner-decision / design-review"
  },
  "status": "reviewing",
  "review_status": "manual-entry-pending-review",
  "manual_validation_pending": true,
  "required_followup": "rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics"
}
```

涉及 source、index 或迁移关系时，再运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

新增 source 优先提供稳定只读 `--check`；没有稳定检查时才使用 `--no-check-reason` 写清原因。registry source object 和 source coverage JSONL row 草稿都应记录 `check`，有 `check` 时不再补 JSON 形式的 `no_check_reason`。

## 中文长期资产

长期文本默认使用简体中文。命令、路径、协议字段、API 名称和代码标识可以保留英文，但必须有中文摘要或中文说明。

长期文档优先写清：

- 背景
- 适用范围
- 结论
- 证据
- 风险
- 下一步

不要长期保留只有命令堆、AI 过程流水账、大段无摘要英文、未区分事实/推断/建议/open items 的材料。

## 新会话恢复

新线程或 AI 恢复时先运行：

```bash
rtk git rev-parse --short HEAD
rtk git status --branch --short
rtk bash ~/knowledge-hub/tools/knowledge-status.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section linking --json
```

恢复顺序：

1. 固定 HEAD、分支和工作区状态。
2. 看 `knowledge-status` 恢复 source、review queue、owner gate 和 automation 状态。
3. 看 `knowledge-final-gate` 判断终态是否通过。
4. 用 `knowledge-search` 和 `indexes/` 找具体正文。
5. 修改后运行 `knowledge-check`，工具/schema/final gate 相关变更再跑 regression/final gate。

## Obsidian

Obsidian 是阅读和手工编辑客户端，不是治理权威。

推荐主要阅读：

- `README.md`
- `notes/`
- `projects/`
- `domains/`
- `indexes/`
- `templates/`

普通使用者不需要日常阅读 `registry/`、`artifacts/manifests/` 和 `tools/`。
