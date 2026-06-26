# Knowledge Hub 硬切换终态设计 Goal

## 最终执行 Goal 指令（推荐引用）

后续线程可直接引用本文件作为长期目标：

```text
Goal: 按 `~/knowledge-hub/docs/goals/knowledge-hub-simplified-final-version.md` 推进 Knowledge Hub 去复杂度硬切换终态。

目标：
- 将 Knowledge Hub 收敛为 Obsidian-friendly Markdown Vault + 最小 registry 账本 + 高风险治理门禁。
- 新增和长期维护内容只使用 canonical 目录：`inbox/`、`notes/`、`projects/`、`domains/`、`sources/`、`registry/`、`indexes/`、`artifacts/manifests/`、`templates/`、`governance/`、`tools/`。
- 项目知识唯一主入口为 `projects/<project>/`；跨项目知识留在 `domains/`；普通和个人笔记进入 `notes/`；资料源边界进入 `sources/` 与 `registry/sources.json`。
- 每个 registered source 必须有 Hub 内 `sources/<source_id>/README.md`、`inventory.jsonl`、`coverage.md`、`source-policy.md`；这是统一管理面，不等于复制 raw 正文。
- 去掉双主路径、重复索引、残留旧入口、不必要 manifest 和过度 owner gate；即使完全人工维护，也能靠 Markdown、最小 registry、search、check 和 review_after 继续运转。
- 所有长期文本、registry、index、manifest 和工具输出都使用 `~` 用户路径形式；禁止写入用户专属绝对路径前缀。

执行规则：
- 所有 shell 命令必须通过 `rtk`。
- 手工改文件必须用 `apply_patch`。
- 默认使用中文和可读结构：结论、证据、风险、下一步分开写。
- 不修改源项目；不写 `~/.codex/memories`；不把 project-specific 内容提升到 `domains/embedded/standards/`。
- AI / Codex 可在 Git 可回滚边界内执行 Hub 本仓 L1/L2 维护；本地 commit 只有在用户明确要求或仓库授权允许且门禁通过后才做。
- owner decision landing、active 提升、memory 写入、源项目修改、远端 Git 状态变更、删除/发布和非 report-only 自动化必须先有明确授权、证据闭环、回滚路径和验证命令。
- 子代理只做边界清晰的只读审计、验证或互不冲突的实现分片；主线程负责整合和最终门禁。

完成标准：
- README、AGENTS、registry/schema、templates、tools README 与本 goal 语义一致。
- `domains/projects/**` 和 `domains/personal/**` 不再作为新增内容入口；旧引用只允许作为 Git 历史或历史 manifest 证据存在。
- registry、sources、indexes 和 Evidence Index 能解释所有 L2/L3 长期资产和高风险动作；`knowledge-check` 能证明 source 主控目录、inventory、owner target 和 raw dump safety 均闭环。
- 普通笔记不被强制 registry；高风险动作必须有 manifest/authorization/owner gate/final gate 证据。
- 核心工具输出不暴露用户专属绝对路径前缀。
- 运行并通过：
  - `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics`
  - `rtk bash ~/knowledge-hub/tools/knowledge-regression.sh --json`
  - `rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json`
  - `rtk git diff --check`

非目标：
- 不兼容旧目录作为长期主入口。
- 不复制 raw session/history 全文到正文层。
- 不把 Obsidian 变成事实权威；Obsidian 只作为阅读和编辑界面，权威仍来自 Markdown 正文、registry、source evidence 和 gate。
- 不新增复杂流程，除非它替代至少两个现有人工步骤并有回归覆盖。
```

## 可直接引用的短 Goal

继续 `~/knowledge-hub` 的去复杂度硬切换。目标是把 Knowledge Hub 收敛为 Obsidian-friendly Markdown Vault、最小 registry 账本和高风险治理门禁：普通内容轻量维护，项目内容统一进入 `projects/`，普通与个人笔记统一进入 `notes/`，跨项目知识进入 `domains/`，source 治理进入 `sources/` 和 `registry/sources.json`，高风险动作才使用 manifest、owner gate、regression 和 final gate。

本目标不兼容旧项目/个人路径作为长期主入口。实施时必须硬切换，并避免双主本、重复索引、残留旧路径和无审计的高风险动作。AI / Codex 默认可在 Git 可回滚边界内执行 Hub 本仓 L1/L2 维护和本地 commit；owner decision landing、active 状态提升、memory 写入、源项目修改、远端 Git 状态变更和非 report-only 自动化必须具备明确授权、证据闭环和回滚路径。即使某段时间完全由人工维护，也必须能按 Markdown、最小待验证块和后续检查命令继续运转。

## 一、最终定位

Knowledge Hub 的终态定位：

```text
Knowledge Hub = Obsidian-friendly Markdown Vault + 最小 registry 账本 + 高风险治理门禁
```

分层职责：

- 阅读层：`README.md`、`notes/`、`projects/`、`domains/`、`indexes/`、`templates/`。
- 治理层：`registry/`、`sources/`、`artifacts/manifests/`、owner gates、review_after。
- 自动化层：`tools/` 中的 check、search、doctor、index plan、regression、final gate。

默认使用体验：

- 普通维护者：写 Markdown、用模板、搜索、跑一次 check。
- 项目维护者：维护 `projects/<project>/`、registry item、review_after 和证据。
- 治理维护者：处理 source coverage、source policy、owner gate、manifest、final gate。
- AI：先读规则和 status，再 search，再读具体文件，最后 check；高风险动作必须先确认授权、scope、证据、回滚和验收命令。

## 二、硬切换目录

终态 canonical 目录如下：

```text
knowledge-hub/
  inbox/                  # 临时草稿、未分类材料、待处理输入
  notes/                  # 普通长期笔记、个人笔记、学习记录
  projects/               # 项目知识唯一主入口
    <project>/
      current/
      decisions/
      validation/
      archive/
  domains/                # 跨项目领域知识，不放项目正文
  sources/                # 人读 source 边界、inventory、coverage 和 source policy
  registry/               # 机器账本
  indexes/                # 可重建导航
  artifacts/
    manifests/            # 高风险治理证据包
  templates/              # 人工模板
  governance/             # 中文治理规则
  tools/                  # 检查、搜索、修复和门禁
```

终态归位映射：

```text
domains/projects/<project>/current/     -> projects/<project>/current/
domains/projects/<project>/decisions/   -> projects/<project>/decisions/
domains/projects/<project>/validation/  -> projects/<project>/validation/
domains/projects/<project>/archive/     -> projects/<project>/archive/
domains/personal/                       -> notes/personal/
```

保留目录：

```text
domains/embedded/    # 跨项目嵌入式领域知识
domains/patents/     # 专利材料
domains/codex/       # Codex 工作流、会话和治理材料
```

新增内容不得继续写入：

```text
domains/projects/**
domains/personal/**
```

旧路径只允许出现在 Git 历史、历史 manifest 或明确标记为历史证据的旧提交说明中。当前 README、registry、indexes、templates、工具默认输出和新文档必须使用新 canonical path。

## 三、非目标与禁止事项

本目标不是继续堆治理复杂度。

默认禁止：

- 不长期维护新旧两套项目路径。
- 不把普通笔记强制登记 registry。
- 不让每条 Markdown 都需要 manifest。
- 不把 `indexes/` 当事实权威。
- 不在 README 复制 schema、template、owner gate、tool README 的完整细节。
- 不新增长期必填字段，除非 `registry/schema.md` 和 `knowledge-check.sh` 已支持。
- 不新增命令入口，除非它能替代至少两个现有人工步骤。
- 不把普通笔记纳入 owner gate。
- 不把历史 archive、handoff、session、memory candidates 当 active facts。
- 不把 project-specific 内容直接提升到 `domains/embedded/standards/`。
- 不把 raw session、history、source code、binary 或 log 以 `copy-body` 方式落入长期正文层；只能登记引用、摘要、artifact-ref、archive-only 或 exclude。

以下高风险动作不是永久禁止，但必须显式授权后才能执行：

- AI / Codex 代签或落地 owner decision。
- 自动把条目标成 `active`。
- 写入 `~/.codex/memories` 或其他长期记忆层。
- 修改 PCR02 或其他源项目文件。
- 执行 `apply-with-review`、发布、删除、发送外部消息等非 report-only 自动化。
- push、merge、release、tag 或其他远端 Git 状态变更。

授权要求：

- 必须能追溯授权来源：当前用户明确指令、项目 owner 明确指令、仓库规则中已登记的 standing delegation，三者至少满足其一。
- 必须记录 `authorized_by`、`authorized_at`、`scope`、`evidence_refs`、`rollback_path` 和 `validation_commands`。
- AI / Codex 不得把自己生成的建议伪装成人类 owner 已确认的结论。
- 授权范围外的动作仍然只能在 Hub 本仓内执行 L1/L2 维护、本地 commit，或生成 plan、diff、manifest、review package、report-only 结果。

## 四、复杂度分级

### L0：临时草稿

路径：

```text
inbox/
```

适用：

- 临时想法
- 未分类资料
- 会话摘要
- 待处理材料
- 工具不可用时的临时记录

要求：

- Markdown only。
- 不需要 registry。
- 不需要 index。
- 不需要 manifest。
- 不需要 final gate。

清理规则：

- L0 只允许短期停留。
- 转长期时进入 L1/L2/L3。
- 不转长期时可以归档或删除；删除前必须确认没有 registry、source-policy、index 或 owner gate 引用。

### L1：普通长期笔记

路径：

```text
notes/
notes/personal/
notes/learning/
notes/debug/
notes/research/
```

适用：

- 学习笔记
- 文章摘要
- 个人经验
- 普通排障记录
- 不承载 owner decision 的资料整理

要求：

- Markdown 优先。
- 中文标题、中文摘要、来源、日期。
- registry 可选。
- 不需要 manifest。
- 不需要 final gate。

边界：

- L1 内容不能自动作为 project current、decision、team standard 或 validation 证据。
- 需要长期复用或团队引用时，升级为 L2。

### L2：受治理长期资产

路径：

```text
projects/<project>/current/
projects/<project>/decisions/
projects/<project>/validation/
projects/<project>/archive/
domains/<domain>/
sources/
```

适用：

- 项目当前事实
- 项目决策
- 项目验证记录
- 跨项目领域知识
- source 边界说明
- 会被 AI 或团队长期复用的内容

要求：

- 必须有 registry item。
- 必须有 owner、status、review_after、summary_zh、evidence_refs。
- 必须通过 `knowledge-check`。
- 通常不需要 manifest。
- 通常不需要 final gate。

边界：

- `projects/<project>/` 内容默认 project-specific。
- `domains/` 内容默认跨项目，但不得从项目内容直接提升，必须有拆分证据。

### L3：高风险治理动作

路径：

```text
artifacts/manifests/
registry/sources.json
indexes/
```

适用：

- source control / source policy 变更
- owner-gated 内容
- owner decision landing
- 团队标准提升
- 自动化能力
- 外部资料批量吸收
- registry/source schema 变更
- 大规模 index/registry 重构
- 阶段性终态收口
- remote Git write

要求：

- 必须有 manifest。
- 必须有 registry/index/Evidence Index 证据链。
- 必须运行 `knowledge-check`。
- 修改工具、schema、终态门禁或 owner gate 时必须运行 regression/final gate。
- 必要时使用 subagents 只读复核。

## 五、Registry 与 Schema 硬切换

终态 registry 原则：

- `registry/items.jsonl` 是长期资产权威账本。
- 普通 L1 笔记不强制登记 registry。
- 一旦登记 registry，就必须满足 `registry/schema.md` 的完整 required fields。
- 新 registry item 的 `path` 必须指向 canonical path。

终态 domain/path 规则：

```text
domain=projects/<project>  -> projects/<project>/**
domain=notes               -> notes/**
domain=embedded            -> domains/embedded/**
domain=patents             -> domains/patents/**
domain=codex               -> domains/codex/**
domain=governance          -> governance/**, registry/**, indexes/**, tools/**, templates/**, docs/goals/**, artifacts/manifests/**
```

废弃：

```text
domain=personal
domains/projects/**
domains/personal/**
```

推荐将个人内容统一为：

```text
domain=notes
path=notes/personal/<file>.md
visibility=personal-local
status=personal 或 reviewing
```

最小人工理解字段：

```json
{
  "id": "",
  "title": "",
  "kind": "",
  "domain": "",
  "path": "",
  "status": "reviewing",
  "owner": "",
  "review_after": "",
  "summary_zh": "",
  "evidence_refs": [],
  "tags": []
}
```

实际落盘仍以 schema 为准；高级字段由工具提示，不要求普通维护者背诵。

## 六、Index、Manifest 与残留治理

### Index

`indexes/` 是可重建导航，不是事实权威。

权威顺序：

```text
registry/sources/source-policy/manifest > generated index > Evidence Index > ad hoc note
```

终态要求：

- index 漏项可被 check 或 index-plan 发现。
- index 不得成为唯一事实来源。
- index 与 registry 冲突时，以 registry 为准。
- 当前 index 中不得把旧 `domains/projects/**` 或 `domains/personal/**` 当 current canonical entry。

### Manifest

Manifest 只用于 L3 高风险动作。

需要 manifest：

- source control / source policy 变更
- owner decision landing
- team standard promotion
- automation governance
- external-source batch absorption
- large-scale registry/index rewrite
- final-state closeout

不需要 manifest：

- 普通笔记
- 个人总结
- 单篇学习记录
- 小型排障 note
- 一次性 debug note

### 残留治理

必须清理或降级：

- README 中重复 schema 的字段权威。
- tools README 中重复人工教程的长流程。
- templates README 中重复工具行为的说明。
- 新旧路径双轨说明或兼容旧入口说明。
- 兼容字段作为新模板默认字段。
- 历史 proof 字段作为新消费方字段。
- 无 registry、无 owner、无 evidence 的长期条目。

允许保留：

- Git 历史中的旧路径。
- 已明确标记为历史证据的旧 manifest。
- 不作为当前入口、默认查询入口或新增归档目的地的 provenance 字段。

## 七、人工完全维护模式

即使 AI、Codex、网络或工具不可用，Knowledge Hub 也必须能由人工继续维护。

人工可做：

- 写 Markdown 正文。
- 使用 `templates/` 中的结构。
- 在正文或相邻维护记录中保留最小待验证块。
- 暂不改 registry，或仅写保守 `reviewing` 草稿。

### 七.2 离线人工维护包

最小待验证块：

```yaml
manual_validation_pending: true
owner: <owner>
date: <YYYY-MM-DD>
status: reviewing
review_after: <YYYY-MM-DD>
source_or_evidence: <path-or-note>
required_followup: rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
```

工具恢复后必须运行完整可复制命令：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-index-plan.sh --section all
```

人工不得做：

- 不得把未验证或未授权条目标成 active。
- 不得伪造 owner decision 或授权来源。
- 不得无记录关闭 owner gate。
- 不得无拆分证据提升 team standard。
- 不得把 archive/session/handoff 写成 current fact。

恢复工具后：

1. 跑 `knowledge-check`。
2. 跑定向 `knowledge-search`。
3. 必要时跑 `knowledge-index-plan`。
4. 只补证据、索引和风险提示。
5. 不覆盖人工结论。
6. 未满足授权和验证前，不自动提升 active。

## 八、最小命令面

README 首屏终态只保留 6 条命令：

```bash
rtk bash tools/knowledge-new.sh ...
rtk bash tools/knowledge-search.sh "<关键词>"
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-status.sh --json
rtk bash tools/knowledge-doctor.sh --json
rtk bash tools/knowledge-final-gate.sh --json
```

日常维护默认只需要前三条：

```bash
rtk bash tools/knowledge-new.sh ...
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-search.sh "<关键词>"
```

使用规则：

- `knowledge-regression.sh` 只用于工具、schema、owner gate、source control 或 final gate 相关变更。
- `knowledge-final-gate.sh` 只用于高风险收口，不用于每条普通笔记。
- `knowledge-index-plan.sh` 默认 report-only，不得自动覆盖人工索引。

## 九、Obsidian 协作

Obsidian 是阅读和手工编辑客户端，不是治理权威。

推荐打开：

```text
~/knowledge-hub
```

Obsidian 主要阅读：

- `README.md`
- `notes/`
- `projects/`
- `domains/`
- `indexes/`
- `templates/`

Obsidian 普通使用者不应日常阅读：

- `registry/`
- `artifacts/manifests/`
- `tools/`

Obsidian 内部链接可以使用 Markdown 链接，但事实状态仍以 registry、source、manifest 和 check 结果为准。

## 十、AI 使用入口

AI 默认读取顺序：

1. `AGENTS.md`
2. `README.md`
3. `rtk bash tools/knowledge-status.sh --json`
4. `rtk bash tools/knowledge-search.sh "<关键词>" --json`
5. 具体文件
6. `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics`

AI 禁止：

- 不默认全仓大范围读取。
- 不把 archive、handoff、memory candidates、owner-ready package 当 active facts。
- 不把 project-specific 内容提升为 team standard。
- 不把 `routing_owner` 当 `reviewed_by`。
- 不在缺少授权记录时代签 owner decision。
- 不在缺少授权记录时写 `~/.codex/memories`。
- 不在缺少授权记录时修改源项目。
- 不在缺少授权记录时执行非 report-only 自动化。
- 不在缺少授权记录时 push、merge、release、tag 或改变远端 Git 状态。

AI / Codex 允许执行的高风险动作：

- 当前用户或 owner 明确授权时，可以代签或落地 owner decision，但必须标明这是 AI / Codex 受托执行，并记录授权证据。
- 当前用户或 owner 明确授权且验证通过时，可以把条目提升为 `active`。
- 当前用户或仓库 standing delegation 明确授权时，可以写入长期记忆层，但必须先有候选、审查记录和回滚方式。
- 当前用户明确把源项目纳入 scope 时，可以修改源项目文件；否则只能修改 Knowledge Hub 内的 canonical 正文、引用、registry、manifest 和 index。
- 自动化可以从 `report-only` 升级到 `apply-with-review`，但必须先产出 dry-run、diff、审批点和 rollback path。
- 当前用户或仓库 standing delegation 明确授权时，可以执行 push、merge、release、tag 或其他远端 Git 状态变更；本地 commit 不需要 L3 授权，但必须在门禁全绿后进行。

## 十一、自动化边界

自动化模式必须显式区分：

```text
read-only
report-only
plan-only
local-commit
apply-with-review
forbidden
```

默认只能：

```text
read-only
report-only
local-commit
```

任何越过 `local-commit` 的 L3 / `apply-with-review` 写入型自动化必须具备：

- dry-run
- diff
- human approval
- rollback path
- memory-write authorization gate
- source-project-write authorization gate

允许的写入型自动化前提：

- `mode=apply-with-review` 或更具体的受控模式。
- `enabled=false` 作为登记默认值，首次执行必须由用户或 owner 明确触发。
- 每次执行记录 `authorized_by`、`authorized_at`、`scope`、`dry_run_result`、`diff_ref`、`rollback_path`、`validation_result`。
- 执行失败不得自动重试破坏性动作，不得自动扩大 scope。

默认禁止静默自动化：

- 删除
- 发布
- push/merge/release/tag
- 提升 active
- 关闭 owner gate
- 写 memory
- 修改源项目
- 发送外部消息

允许静默执行但必须可回滚的 Hub 内维护：

- 改写本仓 registry/index/manifest/template/tools。
- 移动或归并本仓知识文件。
- 门禁全绿后创建本地 commit。

高风险动作在授权后可以执行，但必须进入 L3 治理：manifest、registry/index/Evidence Index 证据、knowledge-check、必要的 regression/final gate。

## 十二、中文长期资产标准

长期 Markdown 默认简体中文。

每篇长期文档至少包含：

- 中文标题
- 中文摘要
- 适用范围
- 结论
- 证据
- 风险
- 下一步

允许保留英文：

- 命令
- 路径
- API 名称
- 协议字段
- 代码标识
- 原文短引用

禁止长期只留下：

- 大段英文原文，无中文摘要
- 命令堆，无结论
- AI 过程流水账
- 未区分事实、推断、建议和 open items 的排障记录

## 十三、实施顺序

硬切换按阶段推进，避免一次性不可恢复大改。

### 阶段 1：目标和入口硬切换

- 重写本 goal。
- 重写 README 首屏。
- 明确新 canonical directories。
- 明确旧路径不再作为新内容入口。
- 不移动正文。

### 阶段 2：schema 和工具硬切换

- 更新 `registry/schema.md` domain/path invariants。
- 更新 `knowledge-new.sh` 默认输出新路径。
- 更新 `knowledge-check.sh` 阻断新 registry item 指向旧路径。
- 更新 `knowledge-search.sh` 和 `knowledge-index-plan.sh` 的恢复视图。
- 更新 templates 默认路径和字段说明。

### 阶段 3：正文和 registry 迁移

- 创建 `projects/`、`notes/`、`sources/`。
- 移动项目正文。
- 移动个人正文。
- 更新 registry paths。
- 更新 indexes。
- 更新 source policy、registry 和 index。
- 不在当前入口保留旧路径。
- 不保留双正文。

### 阶段 4：去残留

- 删除或归档旧路径教程。
- 清理 README / tools README / templates README 重复内容。
- 检查旧 canonical path 是否仍作为 current entry 出现。
- 补负向回归。
- 跑 final gate。

## 十四、验收标准

目标完成时必须满足：

- README 首屏能让普通维护者在 3 分钟内理解日常路径。
- 普通笔记不需要 registry、manifest、final gate。
- 项目知识唯一主入口为 `projects/<project>/`。
- 普通和个人笔记唯一主入口为 `notes/`。
- `domains/` 只承载跨项目领域知识。
- 新 registry item 不允许指向 `domains/projects/**` 或 `domains/personal/**`。
- `indexes/` 明确为可重建导航。
- Obsidian 与 Knowledge Hub 的职责边界清楚。
- AI 默认恢复路径清楚。
- 自动化默认 read-only/report-only/local-commit；授权后可进入 apply-with-review。
- AI / Codex 高风险动作具备授权、证据、回滚和验证记录。
- 中文可读性要求可发现。
- 人工完全维护模式可执行。
- owner gate、source coverage、manifest、regression、final gate 能力不被削弱。
- 不存在新旧路径双正文。

## 十五、实施验证

当前硬切换验收以本次运行的 terminal gate 输出为准；默认不固定旧日期。

2026-06-25 及更早制品只作为历史证据；如果历史制品中仍出现 `needs-owner-review`、`owner-gates-open` 或旧 source 路径，应先判断它是否属于历史 manifest、authorization、automation run 或回归负例，不得反向当作有效状态。

只改本 goal 时：

```bash
rtk git diff --check
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
```

改 README、templates、schema 或 tools 时：

```bash
rtk bash -n tools/knowledge-check.sh
rtk bash -n tools/knowledge-new.sh
rtk bash -n tools/knowledge-search.sh
rtk bash -n tools/knowledge-index-plan.sh
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-regression.sh --json
rtk bash tools/knowledge-final-gate.sh --json
```

硬切换后必须增加负向验证：

- 新 registry item 指向 `domains/projects/**` 应失败。
- 新 registry item 指向 `domains/personal/**` 应失败。
- `knowledge-new.sh --domain projects/pcr02` 必须输出 `projects/pcr02/...`。
- `knowledge-search.sh --domain projects/pcr02` 能找到 canonical 项目内容。
- `indexes/` 中不再把旧路径作为当前入口。
- 当前文档、registry、index、template、tool 输出和 source control 不暴露旧入口。

## 十六、最终口号

```text
普通内容轻量化。
项目内容进 projects。
个人与普通笔记进 notes。
跨项目知识进 domains。
Source 治理进 sources 和 registry。
Registry 是权威账本。
Index 是可重建导航。
Manifest 只服务高风险动作。
正文只维护一份。
AI / Codex 可以受托执行高风险动作，但必须可授权、可审计、可回滚、可验证。
自动化默认 read-only / report-only / local-commit，授权后 apply-with-review。
Obsidian 负责阅读，Knowledge Hub 负责治理。
人工离线也能继续维护。
```
