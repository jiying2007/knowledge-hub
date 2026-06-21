继续 /home/leiwenjun/knowledge-hub 的知识库终态治理。

本次目标是把 Knowledge Hub 建成长期可维护、跨会话可恢复、跨项目可自动关联、人工可独立维护、AI 可辅助治理、自动化受控的统一知识控制面，并完成所有已登记 source 与 PCR02 关键候选 source 的 source coverage、迁移治理和终态闭环。

这不是“继续推进下一步”，而是“终态收口”。请持续推进到以下终态之一：

1. Codex 自动治理终态：
   除真实人工 owner decision 外，所有 source coverage、迁移治理、工具、registry、migration record、index、manifest、README、回归、final gate、跨会话/跨项目关联能力、人工维护入口和自动化边界全部闭环。

2. 全迁移终态：
   如果用户提供有效 owner decision JSONL，则按校验和 landing plan 完成剩余 owner-gated 文档落地，使 final gate 达到 pass。

必须坚持：

- manual-first：人工永远可以添加、更新、归档和复核知识。
- AI-assisted：AI 只能辅助分类、校验、补索引、生成 manifest、发现漂移和降低维护成本。
- automation-gated：自动化默认 read-only / report-only，不越过人工语义决策。
- 不伪造 owner decision。
- 不为了追求 pass 而绕过 owner gate。
- 不把 needs-owner-review 误判为工具失败。
- 不把项目特定内容提升成团队标准。
- 不写 memory。
- 不修改源项目 docs / tools / knowledge / app_product_test / scratch / source tree。
- 不启用自动化写操作。
- 不把“全部迁移”理解成“全部复制正文”。终态是所有资料都有治理状态。

====================
一、最高优先级规则
====================

1. 所有 shell 命令必须使用 rtk。

允许：

- rtk <command> ...
- rtk bash -lc "<command> ..."

禁止裸跑：

- bash / git / rg / sed / awk / python / find / jq 等。

2. 手工创建或修改文件必须使用 apply_patch。

禁止用 heredoc、cat > file、tee、shell 重定向、python write_text 等方式写仓库文件。

3. 不直接写 ~/.codex/memories。

memory candidates 只能进入 manifest / candidate registry，不能进入 active facts。

4. 不修改源项目文件。

包括但不限于：

- /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs
- /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/tools
- /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/knowledge
- /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/app_product_test
- /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/scratch
- /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo 下其他源码、日志、patch、脚本、配置、制品

Knowledge Hub 只维护迁移副本、reference、artifact-ref、registry、manifest、index 和状态。

5. PCR02 project-specific 内容默认只能进入：

- domains/projects/pcr02/current/
- domains/projects/pcr02/archive/
- domains/projects/pcr02/decisions/
- domains/projects/pcr02/validation/
- artifacts/manifests/
- registry/
- indexes/

不得提升到：

- domains/embedded/standards/

除非另有明确 owner review、拆分证据、team-level promotion manifest 和验证记录。

6. 自动化默认 read-only / report-only。

不允许自动删除、发布、提交、提升 active、关闭 owner gate、写 memory、发送外部消息或修改源项目。

7. 正文只维护一份。

其他位置只能使用 index、ref、artifact-ref、manifest、registry、migration record 或 source identity 指向。

8. 不把 session archive、handoff、memory candidates、计划草稿、未验证日志当成 active facts。

9. 发现已有工作区改动时，默认视为用户改动。

不得 revert、覆盖、清理无关变更。

10. 每个结论都必须有证据。

没有命令、manifest、registry、index 或 source evidence，不得声称完成。

====================
二、终态定义
====================

终态分三级。

Level 1：PCR02 docs 终态

- PCR02 `docs/` 下资料全部分类。
- 每个 docs source file 都处于明确状态：
  - copy-first migrated
  - reference-first registered
  - artifact-ref registered
  - archive-only registered
  - no-migration registered
  - owner-ready-no-decision
  - owner-gated pending human decision
- 已迁移正文只有一份 canonical body。
- owner-gated docs 不复制正文、不 active、不关闭 gate。
- 如果 owner decision 未提供，final gate 允许停在 needs-owner-review，但必须只有 owner-gates-open blocker。

Level 2：PCR02 项目关键资料源终态

除 `docs/` 外，PCR02 项目内这些路径也必须纳入 source coverage：

1. `pcr02-project-docs`

- path: /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs
- strategy: existing migration + owner gates

2. `pcr02-project-tools`

- path: /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/tools
- strategy:
  - README.md / AGENTS.md: reference-first 或 owner-gated
  - diag scripts / checks / csv: tool-ref、artifact-ref、validation-tool-ref
  - memory automation scripts: owner-gated、report-only、no-memory-write
  - 不默认复制脚本正文

3. `pcr02-project-knowledge`

- path: /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/knowledge
- strategy:
  - classify-first
  - runbooks / architecture: 可迁移候选
  - governance scripts: tool-ref 或 artifact-ref
  - archive manifests: archive governance
  - .env / secret-like config: secret scan 后 exclusion 或 artifact boundary
  - 不直接提升为团队标准

4. `pcr02-product-test`

- path: /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/app_product_test
- strategy:
  - Markdown docs: classify-first，按 owner 决策 copy-first / reference-first / owner-gated
  - PDF: artifact-ref
  - zip/tgz: artifact-ref
  - ini/config: config-ref 或 artifact-ref
  - C/C++ 源码: 不作为知识正文迁移，只建立 interface / diagnostic / validation reference

5. `pcr02-project-scratch`

- path: /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/scratch
- strategy:
  - archive-only
  - session wrap / context preflight 不进入 active facts
  - memory candidates 不写 memory
  - 可作为历史证据或 handoff 参考

6. `pcr02-project-root-artifacts`

- path: /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo
- scope:
  - 根目录 loose docs / logs / txt / patch / scripts / py / bin
- strategy:
  - .md: classify-first
  - .log / .txt: artifact-ref 或 archive-only
  - .patch: artifact-ref，除非 owner 决策为 patch rationale
  - .bin: artifact-ref，禁止进入文本知识层
  - .sh / .py: tool-ref 或 artifact-ref

7. `pcr02-module-agent-rules`

- paths:
  - cli/AGENTS.md
  - cmd_server/AGENTS.md
  - daemon/AGENTS.md
  - docs/AGENTS.md
  - knowledge/AGENTS.md
  - tools/AGENTS.md
- strategy:
  - module-local owner-gated rules
  - 不得直接提升为 Knowledge Hub 根规则
  - 需要确认 owner、适用模块、review cycle、当前有效性

8. `pcr02-project-agent-config`

- paths:
  - .vscode/codex-tasks-sync.sh
  - .kilo/agent-manager.json
  - .kilo/kilo.jsonc
  - .kilo/setup-script
- strategy:
  - config-ref / artifact-ref
  - 自动化相关内容必须 report-only
  - 不作为 active 团队规则

Level 3：全 Knowledge Hub registered sources 终态

registry/sources.json 中所有 registered source 必须有 source coverage 状态：

- embedded-knowledge
- engineering-archive
- patent-disclosure
- codex-archive
- codex-memories
- pcr02-project-docs
- 后续新增 PCR02 source

每个 registered source 必须有：

- source_id
- source_root
- authority
- write_policy
- migration strategy
- owner
- review_after
- check command 或 no-check reason
- final disposition

每个 source 下资料必须有最终状态之一：

- fully migrated
- copy-first migrated
- reference-first registered
- artifact-ref registered
- archive-only registered
- owner-gated pending decision
- no-migration with reason
- auxiliary-recall-only
- external-tool-owned
- excluded with reason

====================
三、source coverage 不是复制全文
====================

不要把“完成所有迁移”理解为“复制所有文件正文”。

默认策略：

1. Markdown / 可读文本

- 可以 classify-first。
- owner、authority、scope 明确后再 copy-first 或 reference-first。

2. PDF / 图片 / zip / tgz / bin / release binary / SDK / 大附件

- 默认 artifact-ref。
- 不复制正文。
- 记录 hash、size、path、用途、边界。

3. log / txt / session / handoff

- 默认 archive-only 或 artifact-ref。
- 不进入 active facts。
- 抽取事实必须 owner review。

4. patch

- 默认 artifact-ref。
- 如需沉淀，只沉淀 patch rationale / decision，不复制 patch 全文为知识正文。

5. source code / C / C++ / Python / shell

- 默认 tool-ref / implementation-ref / artifact-ref。
- 不把源码全文变成知识正文。
- 只抽取 interface contract、runbook、diagnostic rule、validation evidence。

6. AGENTS.md / local rules

- 默认 owner-gated。
- 只作为 project-local 或 module-local rule reference。
- 不提升为全局规则。

7. config / env / credentials-like files

- secret scan。
- 默认 exclusion 或 artifact boundary。
- 不复制敏感正文。

====================
四、必须先建立基线
====================

开始执行前必须读取关键上下文：

- AGENTS.md
- README.md
- tools/README.md
- registry/sources.json
- registry/projects.json
- registry/items.jsonl
- registry/migrations.jsonl
- indexes/by-owner.md
- indexes/by-review-date.md
- indexes/by-status.md
- indexes/by-topic.md
- indexes/by-project.md
- indexes/by-source.md
- indexes/by-decision.md
- artifacts/manifests/pcr02-project-docs-classification-20260616.md
- artifacts/manifests/pcr02-copy-first-dry-run-20260616.md
- artifacts/manifests/pcr02-copy-first-applied-20260616.md
- artifacts/manifests/pcr02-review-required-resolution-20260617.md
- artifacts/manifests/pcr02-reference-artifact-ref-applied-20260618.md
- artifacts/manifests/pcr02-owner-review-package-20260618.md
- artifacts/manifests/pcr02-owner-review-package-20260618.jsonl
- artifacts/manifests/pcr02-owner-decision-worksheets-20260618.md
- artifacts/manifests/pcr02-owner-decision-worksheets-20260618.jsonl
- artifacts/manifests/pcr02-owner-decision-intake-execution-20260620.md
- artifacts/manifests/knowledge-hub-final-gate-20260620.md
- tools/knowledge-check.sh
- tools/knowledge-status.sh
- tools/knowledge-owner-gates.sh
- tools/knowledge-regression.sh
- tools/knowledge-final-gate.sh
- tools/knowledge-search.sh
- tools/knowledge-new.sh

同时只读扫描 PCR02 candidate source：

```bash
rtk find /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/docs -maxdepth 4 -type f
rtk find /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/tools -maxdepth 4 -type f
rtk find /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/knowledge -maxdepth 4 -type f
rtk find /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/app_product_test -maxdepth 3 -type f
rtk find /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo/scratch -maxdepth 3 -type f
rtk find /home/leiwenjun/work/sigmastar/pcr02_ssc305/SourceCode/sdk/verify/xcrz_sigmastar_demo -maxdepth 2 -name AGENTS.md -type f
```

然后运行基线命令：

```bash
rtk git status --short
rtk bash tools/knowledge-status.sh --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-regression.sh --json
rtk bash tools/knowledge-final-gate.sh --json
```

如果 final-gate 返回 needs-owner-review，先确认 blocker 是否只有 owner-gates-open。
如果还有其他 blocker，必须优先修复非 owner blocker。

====================
五、终态差距地图
====================

执行前必须输出并维护“终态差距地图”。

每条 gap 至少包含：

- gap_id
- gap_type
- source_id
- source_path 或 source_root
- evidence
- 当前影响
- 是否可由 Codex 自动完成
- 是否需要人工 owner decision
- 修复动作
- 写入范围
- 验证命令
- 本轮是否处理
- 处理后状态

gap_type 可取：

- source-coverage
- migration
- owner-review
- registry
- migration-record
- index
- manifest
- jsonl-manifest
- README
- AGENTS
- tooling
- regression
- environment
- final-gate
- source-identity
- duplicate-body
- cross-session-linking
- cross-project-linking
- automation-boundary
- memory-boundary
- manual-maintenance
- Chinese-readability
- artifact-boundary
- secret-boundary

原则：

- 可自动完成的 gap 不要停在建议，必须落地。
- 需要人工 owner decision 的 gap 只能准备签收路径，不能代签。
- 共享文件如 registry、index、schema、README、AGENTS 必须由主 agent 串行修改。
- 每轮处理一组互不冲突的 gap，持续推进直到只剩真实人工 blocker。

====================
六、owner-gated 两阶段流程
====================

阶段 A：没有 owner decision 时

只允许做：

- 生成或补齐 owner-ready package。
- 生成或补齐 owner decision worksheet。
- 生成或补齐 JSONL skeleton。
- 生成或补齐 checklist。
- 生成或补齐 validate-forms 命令。
- 生成或补齐 landing-plan 命令。
- 生成或补齐 source identity。
- 生成或补齐 hard gate / must_not / required fields。
- 登记 registry / migration / index。
- 补回归和 README 入口。
- final gate 显示 needs-owner-review。

禁止做：

- 填 owner_decision。
- 填 reviewed_by。
- 填 reviewed_at。
- 填 source_sha256/source_size 作为 owner 签收字段。
- 填 evidence_refs 冒充 owner 证据。
- 改 worksheet 为 resolved。
- 改 registry 为 active。
- 复制 owner-gated 正文。
- 关闭 owner gate。

阶段 B：用户提供 owner decision JSONL 后

必须按顺序执行：

```bash
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --validate-forms '<owner-decisions.jsonl>' --landing-plan --json
```

只有两条都通过，才允许按 landing plan 落地。

落地后必须运行：

```bash
rtk git diff --check
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-regression.sh --json
rtk bash tools/knowledge-final-gate.sh --json
```

====================
七、长期维护能力
====================

必须让中文开发人员长期维护不成为瓶颈。

需要检查并补齐：

1. 人工新增知识入口

- tools/knowledge-new.sh
- templates
- README 示例
- tools/README 示例
- registry 字段说明
- index 更新说明

2. source coverage 入口

- 如何登记新 source
- 如何分类 source
- 如何选择 copy-first / reference-first / artifact-ref / archive-only / no-migration
- 如何处理新增项目目录

3. 人工复核入口

- by-review-date
- status dashboard
- review_after 规则
- owner 字段
- stale review 诊断

4. 人工检索入口

- knowledge-search
- by-topic
- by-project
- by-source
- by-owner
- by-status
- by-decision

5. 人工 owner 签收入口

- owner-gates summary
- next-open
- checklist
- forms
- forms-jsonl
- validate-forms
- landing-plan

6. 自动化边界入口

- report-only
- no-memory-write
- no-active-promotion
- no-auto-delete
- no-auto-publish
- no-auto-owner-close

7. 质量门禁入口

- knowledge-check
- knowledge-regression
- knowledge-status --strict
- knowledge-final-gate
- git diff --check

8. 中文可读性

- 新增或修改文档优先中文说明。
- 技术标识、路径、命令、字段名保留英文。
- manifest 必须能被中文开发者读懂背景、边界、验证和下一步。
- README 示例必须可直接复制执行。

====================
七.1 长期维护复杂度控制标准
====================

Knowledge Hub 的长期目标不是把所有治理动作都做重，而是让中文开发者和 AI 都能低成本、安全、可恢复地维护。

1. Master Spec 与日常执行分离

- 终态 goal / Master Spec 作为长期规格，不要求每轮完整复述。
- 日常会话只读取：
  - AGENTS.md
  - README.md
  - tools/README.md
  - tools/knowledge-status.sh --json
  - tools/knowledge-final-gate.sh --json
  - 当前 gap 对应 manifest / registry / index
- 新会话恢复 prompt 应控制在：
  - 当前目标
  - 当前 HEAD
  - 当前 blocker
  - 本轮可自动处理 gap
  - 禁止事项
  - 验证命令

2. 小切片不强制全套制品

按风险选择交付物，不机械制造治理噪音：

- 文案修正 / 示例修正：
  - 必需：目标文件、knowledge-check、必要回归
  - 不必新增 manifest，除非它改变治理契约

- 工具契约 / final gate / owner gate / registry 规则变化：
  - 必需：manifest.md、manifest.jsonl、registry item、migration record、核心索引、回归、README 或 tools README

- 新 source coverage：
  - 必需：source registry、coverage manifest、classification manifest、registry/migration/index、source identity、check command 或 no-check reason

- owner-gated source：
  - 必需：worksheet、owner-ready package、forms-jsonl、validate command、landing-plan command
  - 禁止：AI 代签 owner decision

3. AI 与人工职责分离

AI 默认负责：

- source 扫描和分类草案
- source identity / hash / size 记录
- artifact-ref / reference-first / archive-only 草案
- owner-ready package
- JSONL skeleton
- validate-forms 检查
- landing-plan 生成
- registry / migration / index 一致性维护
- README / tools README 入口维护
- regression / final gate 维护
- 中文可读性检查
- 漂移检测和修复建议

人工默认负责：

- owner decision
- 当前有效性判断
- project-local vs team-level 边界确认
- 是否 active
- 是否 no-migration
- 是否 promotion
- 涉密 / 权属 / 合规判断
- review cycle 和 owner 归属确认

AI 不得把人工职责自动补全。

4. 自动化等级

所有自动化必须标注等级：

- L0 read-only：只读查询、检查、报告。
- L1 report-only：生成报告、manifest 草案、landing plan，不写最终状态。
- L2 reviewed-apply：必须人工确认 reviewed manifest 后才写 Knowledge Hub。
- L3 prohibited-by-default：自动删除、发布、提交、提升 active、关闭 owner gate、写 memory、修改源项目。

默认只能使用 L0/L1。
L2 必须有 reviewed manifest、rollback 方案和验证命令。
L3 禁止，除非用户在当前会话明确授权。

5. 索引维护原则

- registry/items.jsonl 是 item 的结构化权威来源。
- registry/sources.json 是 source 的结构化权威来源。
- registry/migrations.jsonl 是迁移状态权威来源。
- indexes/*.md 是人读导航，不应成为唯一事实来源。
- 每个核心索引必须能由工具检查：
  - by-owner
  - by-review-date
  - by-status
  - by-project
  - by-source
  - by-topic
  - by-decision
- 如果某个索引长期需要人工重复维护，应优先增加 read-only index-plan / check，而不是增加人工步骤。

6. 复杂度预算

新增治理机制前必须满足至少一条：

- 解决已重复出现 3 次以上的问题。
- 消除真实 final gate / knowledge-check 漂移。
- 降低人工 owner 签收成本。
- 降低误操作风险。
- 让新会话恢复更可靠。
- 让 source coverage 更可验证。

禁止为了“看起来完整”新增低价值流程、字段、manifest 或脚本。

7. 工具数量控制

新增工具前必须先判断现有工具是否可以扩展解决：

- knowledge-check
- knowledge-status
- knowledge-owner-gates
- knowledge-new
- knowledge-index-plan
- knowledge-regression
- knowledge-final-gate

只有当现有工具职责不匹配，且该流程会重复使用，才新增工具。

8. 人工维护最短路径必须始终可用

README 必须始终保留一条中文最短路径：

- 新增知识
- 新增 source
- owner 签收
- 复核过期项
- 搜索知识
- 跑 final gate

这条路径不能要求维护者理解所有 manifest 历史。

9. owner gate 不等于失败

只要满足：

- knowledge-check pass
- knowledge-regression pass
- final-gate 只有 owner-gates-open
- owner-ready package 完整
- forms-jsonl / validate-forms / landing-plan 可用
- owner-gated 内容未 active
- 未复制 owner-gated 正文

则 Codex 自动治理部分可视为闭环。
剩余状态必须明确标记为人工语义 blocker。

10. 终态报告与每轮报告分离

每轮报告只需包含：

- 本轮处理的 gap
- 改动文件
- 验证命令和结果
- commit
- 剩余 blocker

只有在用户要求“终态审计”或准备关闭目标时，才输出完整 Level 1 / Level 2 / Level 3 审计报告。

====================
七.2 人工维护与离线可维护标准
====================

Knowledge Hub 必须支持人工在 AI 离线、Codex 不可用、网络不可用、现场排障或临时会议后独立添加和维护知识。

AI 是辅助维护者，不是唯一维护入口。

1. 人工可以直接添加知识

人工允许直接创建或修改以下内容：

- domains/projects/<project>/current/
- domains/projects/<project>/archive/
- domains/projects/<project>/decisions/
- domains/projects/<project>/validation/
- domains/embedded/ 下已明确属于 team-level 的 runbook / decision / standard
- domains/patents/
- domains/personal/
- artifacts/manifests/
- registry/items.jsonl
- registry/migrations.jsonl
- indexes/*.md

但必须遵守：

- 正文只维护一份。
- 新增内容必须有 owner。
- 新增内容必须有 review_after。
- 新增内容必须有 status。
- 新增内容必须能被 registry/index 找到。
- 涉及项目资料时必须标明 project id。
- 涉及 source 时必须标明 source id 或 no-source reason。
- 不确定是否 active 时，默认 reviewing。
- 不确定是否团队级时，默认 project-specific 或 personal，不提升到 team standard。

2. 人工新增知识最小必填字段

人工新增 registry item 至少要填写：

- id
- title
- kind
- domain
- path
- scope
- visibility
- status
- owner
- source
- validation_refs
- tags
- review_after
- promotion
- review_status
- created_at
- updated_at

如果暂时没有完整证据：

- status 使用 reviewing
- review_status 使用 manual-entry-pending-review
- validation_refs 至少包含人工可复核路径或说明
- promotion 使用 none

禁止为了省事把未验证内容设为 active。

3. 人工新增知识最短路径

人工新增一条知识时，最短流程是：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-new.sh --kind <kind> --domain <domain> --id <id> --path <path> --owner <owner>
```

然后人工执行：

1. 从 templates/ 复制合适模板到唯一正文位置。
2. 写正文，优先中文。
3. 在 registry/items.jsonl 新增 item。
4. 在必要索引中登记：
   - indexes/by-owner.md
   - indexes/by-review-date.md
   - indexes/by-status.md
   - 如涉及项目：indexes/by-project.md
   - 如涉及 source：indexes/by-source.md
   - 如涉及主题：indexes/by-topic.md
   - 如涉及决策：indexes/by-decision.md
5. 如是迁移或引用，补 registry/migrations.jsonl。
6. 运行：

```bash
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

如果工具不可用，人工至少保留 TODO 标记：

```text
manual_validation_pending: true
reason: tools unavailable / AI unavailable / offline field note
required_followup: run knowledge-check and update registry/index
owner: <owner>
review_after: <date>
```

4. 人工生成知识也必须有来源类型

人工写入的知识不要求来自 AI，也不要求来自已有 source。

source 字段可以是：

```json
"source": {
  "type": "manual",
  "from": "field-debug / meeting / code-review / lab-test / owner-decision / design-review"
}
```

常见人工来源：

- field-debug
- lab-test
- meeting
- code-review
- design-review
- owner-decision
- release-review
- production-feedback
- customer-feedback
- personal-note

5. 人工内容默认状态

人工新写内容默认状态规则：

- 有验证、有 owner、有适用范围、有 review_after：可设为 reviewing
- 已经团队确认并有证据：可设为 active
- 历史记录、现场日志、session、临时观察：设为 archived 或 reviewing
- 不确定事实：不得 active
- 不确定边界：不得 promotion
- 不确定是否团队通用：不得进入 domains/embedded/standards/

6. 人工写入也要保留中文可读性

人工文档优先使用中文说明：

- 背景
- 适用范围
- 结论
- 操作步骤
- 验证证据
- 风险
- 下一次复核时间

技术标识保留英文：

- 命令
- 路径
- API
- 寄存器
- 文件名
- 字段名
- commit id
- source id
- project id

7. AI 回来后不能覆盖人工内容

AI 恢复后必须把人工改动视为用户改动。

AI 可以做：

- 校验 registry/index 是否一致
- 补 manifest
- 补 migration record
- 补 source identity
- 补 search/index 入口
- 改善中文可读性
- 提出风险和缺字段
- 生成修复 patch

AI 不得做：

- 自动重写人工结论
- 自动删除人工记录
- 自动把人工 reviewing 改 active
- 自动关闭 owner gate
- 自动把人工项目结论提升成团队标准
- 自动把人工草稿写入 memory

8. 离线人工维护包

Knowledge Hub 应保留一个离线可用的人工维护包：

- README.md：人工最短路径
- tools/README.md：工具命令说明
- templates/：正文模板
- registry/schema.md：registry 字段说明
- indexes/README.md 或等效说明：索引维护说明
- tools/knowledge-new.sh：只读新增向导
- tools/knowledge-check.sh：恢复后校验入口

即使 AI 不可用，人工也能按模板写入；AI 恢复后再做一致性校验和治理补齐。

9. 人工维护不应成为瓶颈

人工只负责语义判断和必要事实记录。

人工不应被迫理解全部治理历史。

因此 README 必须始终保留 5 条最短路径：

- 新增一条知识
- 新增一个 source
- 归档一条历史记录
- owner 签收一个 gate
- 跑一次终态检查

复杂治理细节放在 manifest 和 tools 中，不压到人工日常流程上。

10. 人工生成知识的终态要求

人工生成知识只要满足以下条件，就可以作为长期资产：

- 有唯一正文位置。
- 有 registry item。
- 有 owner。
- 有 review_after。
- 有 status。
- 有 source 或 manual source reason。
- 有至少一个可复核证据或 no-check reason。
- 能通过 knowledge-check。
- 没有 secret。
- 没有错误提升边界。

====================
八、跨会话自动关联
====================

Knowledge Hub 必须支持 Codex 在不同会话恢复上下文。

需要确保：

1. 新会话入口明确：

- AGENTS.md 指向 Knowledge Hub 的定位、边界、命令、禁止事项。
- README.md 提供快速恢复命令。
- tools/README.md 提供维护命令。

2. 状态可恢复：

- rtk bash tools/knowledge-status.sh --json
- rtk bash tools/knowledge-final-gate.sh --json
- 能告诉 agent 当前是否 pass、是否 needs-owner-review、下一步命令是什么。

3. 项目可恢复：

- 通过 project id 找到 PCR02 相关 current / archive / decisions / validation / manifests。
- indexes/by-project.md 必须覆盖 PCR02。
- registry/items.jsonl 必须有 domain/project/scope/source。

4. source 可恢复：

- registry/sources.json 记录 source_id。
- indexes/by-source.md 能从 source 找到迁移、引用、owner gate、source identity。
- 每个 source_path 有最终状态。

5. topic 可恢复：

- indexes/by-topic.md 覆盖 migration、owner gate、PCR02、tools、knowledge、product-test、scratch、diag、ASAN、memory auto-curation、DVR、motor MCU、governance、automation、regression、patent、codex archive。

6. decision 可恢复：

- indexes/by-decision.md 能从 owner worksheet、project decision、migration decision 找到对应证据。
- owner decision 未签收时必须明确 no decision generated。

7. handoff 可恢复：

- 如上下文过长，生成 handoff manifest。
- handoff 区分 stable / dynamic / evidence / excluded context。
- 不写 memory。

====================
九、跨项目自动关联
====================

Knowledge Hub 必须支持不同项目之间通过 registry/index/ref 自动关联，而不是复制正文。

需要确保：

1. 每个项目有唯一 project id。
2. 每个来源有唯一 source id。
3. project-specific 内容只能在项目域内 active。
4. team-level 内容必须有 promotion manifest。
5. 跨项目共用知识只能通过：
   - domains/embedded/ 下的 team-level runbook / standard
   - registry tags
   - by-topic index
   - by-source ref
   - by-decision ref
   - artifact-ref
6. 不允许把 PCR02 本地路径、命令、版本、SDK、脚本默认泛化为团队标准。
7. 如果发现可复用方法论，如 ASAN 通用方法，只能先生成 team-candidate boundary，不得直接提升 active standard。
8. 跨项目关联必须保留 provenance：
   - source_id
   - source_path
   - source_sha256
   - migration_manifest
   - owner
   - review_after
   - promotion_decision

====================
十、subagents 使用规则
====================

用户要求使用 subagents 时，必须使用，但要遵守单写者模型。

适合并行的任务：

- 只读审查 source coverage 缺口。
- 只读审查 CLI 契约。
- 只读审查 registry/index 漏登。
- 只读审查 README / tools README 入口。
- 只读审查 regression 缺口。
- 只读审查 owner gate 签收包。
- 只读审查 cross-session / cross-project linking。
- 只读审查中文可读性和长期维护瓶颈。
- 只读审查 artifact / secret / automation boundary。

不适合并行写入：

- registry/items.jsonl
- registry/migrations.jsonl
- registry/sources.json
- registry/projects.json
- indexes/*.md
- README.md
- AGENTS.md
- schema / shared tools / final gate

要求：

- 每轮最多 2 到 4 个 subagent。
- subagent 默认 WRITE: NONE。
- subagent 输出 STATUS / CHANGES / RISKS / VERIFY / OPEN。
- 主 agent 汇总后串行 apply_patch。
- 不得让多个 agent 同时改共享文件。

====================
十一、每个落地切片的交付物
====================

按风险选择交付物，不机械制造治理噪音。

1. 文案修正 / 示例修正：

- 必需：
  - 目标文件
  - rtk git diff --check
  - rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
- 视影响补：
  - README
  - tools/README
  - regression
- 不必新增 manifest，除非改变治理契约。

2. 工具契约 / final gate / owner gate / registry 规则变化：

- 必需：
  - artifacts/manifests/<id>.md
  - artifacts/manifests/<id>.jsonl
  - registry/items.jsonl
  - registry/migrations.jsonl
  - indexes/by-owner.md
  - indexes/by-review-date.md
  - indexes/by-status.md
  - indexes/by-topic.md
  - tools/knowledge-regression.sh
  - README 或 tools/README
  - Evidence Index

3. 新 source coverage：

- 必需：
  - registry/sources.json
  - coverage manifest
  - classification manifest
  - registry/migrations.jsonl
  - indexes/by-source.md
  - indexes/by-project.md（如涉及项目）
  - source identity
  - check command 或 no-check reason

4. owner-gated source：

- 必需：
  - worksheet
  - owner-ready package
  - forms-jsonl
  - validate command
  - landing-plan command
  - registry / migration / index
- 禁止：
  - AI 代签 owner decision

所有切片都必须明确边界：

- 不改源项目文件。
- 不生成 owner decision。
- 不关闭 owner gate。
- 不启用自动化写操作。
- 不写 memory。
- 不提升 PCR02 project-specific 到 embedded standards。
- 不复制 artifact/log/binary/session 作为知识正文。

====================
十二、验证与提交
====================

每轮修改后必须运行：

```bash
rtk git diff --check
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-regression.sh --json
rtk bash tools/knowledge-final-gate.sh --json
```

如果修改 README / tools / manifest / registry / index，也要按影响运行定向命令，例如：

```bash
rtk bash tools/knowledge-search.sh "PCR02" --json
rtk bash tools/knowledge-owner-gates.sh --source-id pcr02-project-docs --summary --json
rtk bash tools/knowledge-status.sh --json
```

如有文件改动且验证符合预期，提交：

```bash
rtk bash ~/codex/scripts/commit-ready.sh
rtk git add <本轮相关文件>
rtk git commit -m "docs(governance): <中文动词短句>"
```

提交后复验：

```bash
rtk git status --short
rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash tools/knowledge-final-gate.sh --json
```

如果 final gate 返回 1，但 status 是 needs-owner-review 且唯一 blocker 是 owner-gates-open，可以作为 Codex 自动治理终态；必须在最终说明中明确这是人工语义 blocker，不是工具失败。

====================
十三、最终输出要求
====================

每轮普通输出只需包含：

1. 本轮处理的 gap。
2. 改动文件。
3. 验证命令和结果。
4. commit。
5. 剩余 blocker。

只有在用户要求“终态审计”或准备关闭目标时，才输出完整报告：

1. 当前终态级别。
2. 当前 HEAD commit。
3. 工作区状态。
4. 验证结果。
5. PCR02 docs 迁移状态总览。
6. PCR02 其他 source coverage 状态。
7. 全 registered source coverage 状态。
8. 剩余 owner gate 清单。
9. 长期维护入口。
10. 跨会话恢复入口。
11. 跨项目关联入口。
12. 剩余真实风险。

====================
十四、当前已知事实
====================

仓库：

- /home/leiwenjun/knowledge-hub

已知 registered sources：

- embedded-knowledge
- engineering-archive
- patent-disclosure
- codex-archive
- codex-memories
- pcr02-project-docs

已知 PCR02 candidate sources：

- pcr02-project-tools
- pcr02-project-knowledge
- pcr02-product-test
- pcr02-project-scratch
- pcr02-project-root-artifacts
- pcr02-module-agent-rules
- pcr02-project-agent-config

已知 PCR02 docs 已完成：

- PCR02 32 个项目 docs 已分类。
- 23 个低风险 docs 已 copy-first 迁移。
- README.md 已登记为 reference-first，不复制正文。
- prog-tool-ci-smoke.session 已登记为 artifact-ref，不复制脚本正文。
- 剩余 7 个 review-required 项已生成 owner-review package。
- 已有 owner-ready package / intake execution / final gate / regression helper 等治理资产。
- 当前 final gate 预期仍可能是 needs-owner-review，因为 7 个 owner gate 需要人工 owner decision。

7 个 PCR02 docs owner-gated 阻塞项：

- AGENTS.md
- standards/diag-command-metadata-standard.md
- runbooks/asan-debug-guide.md
- runbooks/memory-auto-curation-guide.md
- plans/2026-06-15-dvr-record-proto-sensor-decoupling-plan.md
- reports/2026-05-29-motor-mcu-debug-record.md
- reports/2026-06-16-dvr-record-replay-session-archive.md

这些不得被 Codex 自行签收或提升 active。

====================
十五、执行策略
====================

不要一次只做建议。
请循环执行：

1. 建立基线。
2. 生成终态差距地图。
3. 选择可自动完成的最高价值 gap。
4. 使用 subagents 做只读审查。
5. 主 agent 串行落地。
6. 补必要 manifest / registry / source registry / index / README / regression。
7. 运行验证。
8. 提交。
9. 复验。
10. 继续下一组 gap。

直到满足：

- 全迁移终态；
- 或 Codex 自动治理终态，且唯一剩余事项是真实人工 owner decision。
