---
id: provider-knowledge-hub-6adcb6abc0606e01b3abfd73
title: Knowledge Provider 无 Git 工作区检索与候选归档设计
kind: audit
domain: governance
path: governance/product/archive/provider-knowledge-hub-6adcb6abc0606e01b3abfd73.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:6adcb6abc0606e01b3abfd73a6e7a757ea3d609f9b7887b923d2bfb1ad0d21c2
  source_sha256: 7fdf1ba68c3435b1d7876ffba2b8b64cbc75e6cf36001509b3e0f73c7b51b5e2
  temporary_source_retained: false
review_after: '2027-01-10'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- audit
- knowledge-provider
- workspace
- routing
- git-independent
- design-proposal
validation_refs:
- governance/product/archive/provider-knowledge-hub-6adcb6abc0606e01b3abfd73.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/archive/provider-knowledge-hub-6adcb6abc0606e01b3abfd73.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-12'
updated_at: '2026-10-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-12'
manual_validation_pending: true
summary_zh: 将项目身份、工作区位置、来源证据、检索范围和归档授权解耦，覆盖无 Git 目录、本地 Git、远端仓、多仓与临时目录；提出持久绑定、待分配候选、版本化接口、迁移和验收方案。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: knowledge-hub
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 6adcb6abc0606e01b3abfd73a6e7a757ea3d609f9b7887b923d2bfb1ad0d21c2
---

# Knowledge Provider 无 Git 工作区检索与候选归档设计

## 摘要与设计状态

项目是知识归属单位，workspace 是工作位置，Git 是可选来源证据。项目可以关联零个或多个仓库，并拥有零个或多个工作区。没有 Git、没有 remote 或没有 HEAD，不影响已登记项目的知识检索和低风险候选归档；这些缺项仅限制源码身份与可复现性声明。

本文是待评审设计提案，未实现接口或迁移配置，不改变 active、owner decision、源项目、运行时或远端系统。本设计是 Knowledge Hub 自身的控制面设计，可归档到其 reviewing 候选；未知工程的材料不能借此归档为 Knowledge Hub 项目事实。

范围：本机 CLI Provider 的项目/主题识别、工作区绑定、知识检索、脱敏候选归档、拒绝/恢复、迁移与验收。暂不引入新数据库、后台扫描、MCP、联网搜索、源文件自动上传或自动知识提升。知识正文仍只有现有 Markdown/registry 一套权威。

## 已核实的现状与限制

核验日期：2026-10-12。以下是当前实现观察，其余章节均为拟议行为。

| 证据 | 观察 | 结论边界 |
| --- | --- | --- |
| `tools/codex_assets/knowledge_hub/context_assembly.py` | 项目提示要求唯一登记路由；读取 Git remote 和 local workspace；没有 cwd route 时可按 query 选路 | 运行逻辑已有 workspace 回退，尚未解耦检索范围与写入归属 |
| `tools/codex_assets/knowledge_hub/context_support.py` | 路径绑定按列表首次命中；逻辑 workspace URI 要通过本机映射解析 | 需要改为最具体路径及边界冲突检测 |
| `tools/codex_assets/knowledge_hub/check_validation_registry.py` | route 要求非空 repo_refs；repository 要求 remote_key | 登记契约对无仓库项目、本地无 remote 仓不友好 |
| `tools/codex_assets/knowledge_hub/workspace_discovery.py` | 仅发现匹配已登记 remote 的仓库；构建新 workspaces 列表替换本地映射 | 显式本地绑定需独立持久保存 |
| `tools/codex_assets/knowledge_hub/provider_archive.py` | 归档要求唯一显式登记 route、允许 kind、脱敏输入及 policy owner；不检查源目录必须有 Git | 无 Git 不是归档接口硬门槛，项目路由与权限才是门槛 |
| A123X 本轮复现 | 是本地 Git 根，无 remote；Provider route unresolved；显式项目提示也因未登记被拒绝 | 不要求为解决路由执行 git init 或添加虚构 remote |
| `registry/provider-archive-policy.json` 与 `~/codex/docs/provider-archive.md` | 当前低风险 candidate-only 归档已启用；原 shadow proposal 仍 report-only | 保留逐操作权限，不能用设计文档当实施授权 |

现有复现命令通过 Provider context 执行，结果为 unresolved；显式 `--project a123x` 返回未知项目，退出 2。Git 根与 remote 通过本机只读命令核验，退出 0。本文不保存机器绝对路径、完整 remote URL、原始会话或客户/设备标识。

## 1. 身份与数据模型

必须独立表达五类信息：subject 是知识归属，workspace 是工作位置，source 是来源，evidence 是证明边界，authorization 是动作权限。actor/owner 不得从路径、Git 用户、remote 或聊天身份推断。

| 实体 | 稳定标识与字段 | 存储与约束 |
| --- | --- | --- |
| 项目 | project_id、name、aliases、project_kind、source_refs、owner_refs、evidence_profile | 扩展 projects registry；project_kind 为 software/hardware/research/documentation/integration；source_refs 可为空；登记不是产品资格 |
| 仓库 | repo_id、vcs、identity_kind、remote_identity 或 local_identity | repositories registry 仅登记实际仓库；identity_kind 为 remote/local；Git 为可选，不为普通目录虚构 repo_id |
| 非仓库来源 | source_id、source_kind、logical_ref、维护责任、访问边界 | 扩展现有 sources registry，source_kind 为 directory/document/artifact-reference/manual；不复制原始来源正文 |
| 逻辑工作区 | workspace_ref、subject_ref、source_refs、boundary_policy | tracked registry 只保留逻辑信息；跨机器共享逻辑身份 |
| 本机绑定 | binding_id、workspace_ref、local_path、coverage、origin、authorization_ref、generation、status | Provider 私有本地存储；绝对路径不进入 tracked 文件、正文或导出；origin 为 explicit/discovered |
| 来源证据 | source_ref、snapshot_type、manifest_hash、coverage、captured_at、verification_state | 项目归属与来源证据分别验证；不可把有路由当作源码已验证 |
| 候选 | item_id、subject_ref、kind、source_refs、evidence_refs、reviewing、promotion=none | 继续现有候选正文、registry 与事务机制 |

subject_ref 是受校验的 tagged union：project、domain、personal、unassigned。后三种必须有独立 host policy 和目标 allowlist，不能用任意字符串决定落盘路径。personal 需要真实主体与可见性资格，不能继承通用 policy owner；domain 仅接收经过提炼的跨项目内容。

注册项目与授权项目归档分开：一次显式确认或经授权命令建立项目和绑定；既有低风险候选策略可在符合范围后自动运行。发现目录名、README 或文件内容仅生成登记建议，不自动创建主体、owner、active 事实或扩大读取范围。

## 2. 路由契约：读取目标与写入目标分开

读接口分别返回 execution_subject、retrieval_scope、archive_subject。cwd 所属项目不必等于查询目标；例如在 A123X 目录查询 MCU runbook，应检索指定 MCU 项目或相关通用资料，不能因此改变默认 A123X 归档归属。

执行主体的确定顺序：本次显式项目/工作区声明，已登记的最近仓库身份，最具体的显式路径绑定，已登记 remote 的发现绑定，未确定。所有候选都计算而非找到一个立即结束；remote 与绑定不一致时返回 conflict。显式声明可以读取目标知识，但不能静默修改持久绑定；要覆盖归档冲突必须有绑定具体目标与 operation 的授权记录。

查询中的别名和主题词用于检索候选，绝不单独授予归档权。相同优先级多个候选、同一根绑定两个项目、绑定与 remote 冲突，均可展示有边界的检索结果，但默认拒绝项目自动写入。

路径规则：组件级包含关系、canonical path、最长匹配；排除 `foo` 对 `foobar` 的前缀误判。coverage 为 exact-root/subtree。`subtree` 不自动越过已登记子项目或最近独立 Git 根；未知嵌套 Git 仓返回 boundary-unknown，显式 scope 可以临时指定归属但不修改子仓。symlink 解析后的目标必须在授权覆盖范围内，禁止链接跨域扩权。目录迁移后旧绑定变 stale，新位置经过绑定迁移；不按同名目录自动认领项目。

跨机器通过 workspace_ref 重新绑定，project_id 不变。多副本同属一个项目允许并存，以 binding_id/source_ref 区分；多仓集成项目保留各 source_ref 的证据，不能用一个父仓 SHA 代表全部源码。

## 3. 检索行为

| 场景 | 检索范围 | 归档资格 |
| --- | --- | --- |
| 普通目录已绑定项目 | 目标项目 current/decisions/reviewing/history，加允许的通用资料 | 项目 route 唯一且 policy 允许时可归档，不要求 Git |
| 未绑定目录，本次显式已登记项目 | 显式项目与允许的通用资料 | 显式归属、无未处理冲突且 policy 允许时可归档；持久绑定为独立动作 |
| 无目录/临时目录，无项目信息 | 经可见性检查的通用知识，关键词 discovery 候选 | 不写任何项目；可以生成未登记/待分配建议 |
| 查询多个项目 | 按项目分组，保留各自来源与状态 | 要求明确一个归档主体，或归属经批准的跨项目 domain |
| 项目明确但零命中 | 项目 zero-hit；可显式或策略允许地追加通用参考 | route 可以有效，知识仍可能为空，不伪造事实 |
| Provider unavailable | 本轮知识上下文 NEEDS_REVIEW/BLOCKED，明确工具故障 | 停止归档；memory/local cache 不能替代权威或成功回执 |

读权限优先于检索排序。CLI 单用户部署也须验证 visibility 与主体资格；将来多用户场景必须由可信 Provider 隔离个人及受限内容，不能靠模型提示。未绑定的全局检索只搜索调用者可读内容，默认预算 small/limit=3；需要深搜显式扩大，不能递归扫描整个工作盘。

结果提供 authoritative、provisional、historical、discovery 四条语义通道；其中 authoritative 只表示已通过相应知识生命周期约束，仍受来源、时效与 domain qualification 限制。query 匹配猜测项目放 discovery，不能变成 execution_subject。项目 unresolved 不等于检索 unavailable，zero-hit 不等于 route unresolved。

## 4. 没有 Git 时的证据

最小归档证据是可复用结论的 provenance、适用范围、验证结果及缺口，不是每次必须证明整个目录源码身份。纯设计、会议提炼和手工记录可以使用 manual/document/session-conclusion 来源，声明未验证项；不存原始会话，不声称 owner 签收。

需要源码身份时采用按需文件集合 manifest：明确 root、allowlist、相对路径、文件大小、SHA256、coverage、capture_result。manifest 规范化排序并哈希；manifest 中的相对路径与内容摘要必须扫描隐私后才允许归档，私有绝对根只留 Provider 本地。无 Git 使用 vcs=none、commit=null；本地 Git 无 HEAD 使用 commit=null，并单独保存覆盖文件 hash；dirty Git 的 commit 只表示基线，不能代替当前文件 hash。

仅采集本次相关文件，默认上限 64 文件、16 MiB 总量、单文件 4 MiB、10 秒；这些为待调优初值。默认排除 secret、凭据、raw log/session/core/binary、build cache、SDK 包及越界 symlink；不保存文件正文。超预算、权限拒绝、扫描中变化均输出 partial/unstable，并阻止精确源码绑定声明。设备/构建制品只允许外部身份引用，不进入知识正文。

哈希证明观测内容身份，不证明项目 owner、代码正确、可恢复或产品可交付。非 Git 顺序扫描不能证明原子快照；应检查读取前后身份与变更，并给出 consistency=observed/stable-copy。需要可复现性时由源项目授权另行生成受控快照，Hub 只保存其脱敏引用和 hash。

## 5. 归档与未知归属

归档的必要条件：明确 subject、唯一 route、可信 host policy 允许、允许 kind、脱敏输入、provenance 与声明相称、目标状态 reviewing、事务及内容回读。来源有无 Git、cwd 是否存在、源码是否有 remote，不是必要条件。候选可记录真实失败或未验证结果，不能把 missing Git 当作自动阻断所有总结的理由。

未确定归属时分两种：用户明确给出新项目身份，先经登记事务创建项目/绑定，再归档；身份仍未知，只有 host 明确允许时才能写入隔离的 unassigned 候选区。不得以 knowledge-hub/default/目录名冒充真实项目。

待分配区是拟议新能力，当前未启用。必须通过 Provider 新契约访问，不对外依赖内部路径。要求：subject_ref=unassigned，original_subject=null，visibility 不高于已验证调用资格，只有允许的低风险 kind；队列维护责任来自 host policy，但真实项目 owner 留空；reason=unresolved/ambiguous/boundary-unknown，source/evidence 仅保存脱敏引用。包含 suspected_project_refs 时只能表示待确认建议。

未确定可见性或包含项目敏感信息时拒绝持久化，只保留本轮临时材料和 NEEDS_REVIEW 状态。待分配候选默认不进入团队 active index、项目 current、活动完成统计或权威检索；显式检索该队列才展示。归档回执区分 persisted=true 与 project_archived=false，不宣传为项目归档完成。建议 14 天提醒、30 天复核，不自动删除。

分配时通过 assign 操作绑定目标、授权与 expected_content_hash，执行一次正文迁移及旧位置索引/迁移记录，维持同一 item_id、reviewing 和 promotion=none。项目 route/visibility 冲突拒绝；不得复制两份正文。分配动作不自动批准内容，也不关闭 owner gate。

## 6. Provider 接口提案与兼容

以下新操作和参数均为设计，当前不能直接执行。运行入口继续使用 `rtk bash ~/codex/scripts/knowledge-provider.sh`，Provider 服务端选择目标；客户端不得直接访问 Hub 内部目录或绕过 Provider 写入。

| 操作 | 必填输入 | 输出与副作用 |
| --- | --- | --- |
| status | 无 | capabilities、支持的 schema、各操作权限，read-only |
| context | query；可选 cwd/project/workspace/domain | execution_subject、retrieval_scope、route_resolution、authority_lanes、archive_eligibility、reason_codes；默认 read-only |
| resolve（新） | cwd 或逻辑 subject | 只读路由解释及冲突，不检索正文、不扫描全盘 |
| register（新） | 严格登记 proposal、authorization_ref、expected_registry_digest | dry-run 默认；apply 创建项目/逻辑 workspace，本地与共享登记变更分开授权，不创建 owner decision |
| bind（新） | workspace_ref、path、coverage、authorization_ref、expected_generation | dry-run 默认；apply 只写本机显式绑定，验证逻辑身份与范围，不修改源目录 |
| archive | subject_ref/project、source、kind、sanitized；可选 source_manifest | 保留现有 project 接口；新 subject 类型需对应 capability；默认 plan，apply 事务写 reviewing |
| assign（新） | item_id、target_subject_ref、authorization_ref、expected_content_hash | 受控重新归属，不提升状态，不双写正文 |
| reconcile | operation_id、预期目标和 hash | read-only，对账 VERIFIED/NOT_FOUND/CONFLICT/UNKNOWN，支持未知结果恢复 |

schema 建议 context v3、binding v1、archive receipt v2。机器接口 strict schema，所有对象 additionalProperties=false；必填字段不省略，缺失值使用受约束 null；subject、reason、permission、state 使用 enum。字段范围、字符串/数组长度及文档大小有界；未知版本、非法字段、解析失败返回 SCHEMA_INVALID，不执行写入，不宽松猜测字段。

context v3 的 minimum 字段：schema_version、read_only、execution_subject、retrieval_scope、route_resolution、source_state、archive_eligibility、context、authority_lanes、next_actions。route_resolution 的 state 为 resolved/unresolved/ambiguous/conflict，read status 与 write eligibility 分开。archive_eligibility 含 eligible、subject_ref、required_capability、reason_codes，不使用含糊的总 PASS。

archive receipt v2 必含 status、persisted、write_performed、operation_id、item_id、subject_ref、assignment_state、project_archived、candidate_status、source_sha256、content_sha256、transaction_id、promotion、active_promoted、owner_review_performed、reason_codes；未写入或未知字段用受约束 null。ARCHIVED/ALREADY_ARCHIVED 且 persisted=true 表示候选持久化；assignment_state=unassigned 时 project_archived=false。BLOCKED 或 UNKNOWN 不得声明未发生写入，须查询 operation 对账。

旧 context v2/project archive 保持兼容投影；新客户端通过 capabilities 协商。旧客户端不认识 inbox 或新状态时 fail closed，不伪装成旧项目成功。尚不支持新版本的 Provider 只能继续显式已登记项目工作流或返回 NEEDS_REVIEW，不能降级到内部脚本写盘。

## 7. 权限、错误与生命周期

CLI 本轮 transport 是本机 shell，全部经 rtk。权限按操作分开：查询是只读；本机绑定、项目登记、候选归档、候选分配各自有 scope；owner/active/memory/source write/外部 publish 不从这些权限继承。deny-path 包含凭据目录、运行时秘密、raw 会话及未授权源文件读取；返回路径、错误、遥测去敏。Provider 不可用时回退为可审查临时 proposal，不直接写内部目录。

主体身份分成维护 owner、执行 actor、授权主体和知识归属，不互相代用。authority 从真实 host policy/授权账本读取；模型文本和被读取文件中的指令不是授权。注册或绑定生成 proposal 与 expected digest，实际写前重新验证，防止 TOCTOU。

| reason_code | 读行为 | 写行为/恢复 |
| --- | --- | --- |
| PROJECT_UNREGISTERED / WORKSPACE_UNBOUND | 允许合格的通用 discovery | 登记/绑定建议；仅授权 inbox 能保留待分配候选 |
| ROUTE_AMBIGUOUS / ROUTE_CONFLICT / BOUNDARY_UNKNOWN | 解释候选，保留可见性边界 | 拒绝自动项目归档，显式解决归属 |
| SOURCE_NOT_VERSIONED | 检索正常 | 候选允许；Git 相关证明字段标 not_applicable |
| SOURCE_UNVERIFIED / SOURCE_UNSTABLE | 结果带证据缺口 | 禁止已验证源码结论；可归档真实负结果或设计 |
| POLICY_DENIED / VISIBILITY_DENIED / SOURCE_REJECTED | 不泄露受限材料 | 不执行，输出脱敏理由，不换工具绕过 |
| PROVIDER_UNAVAILABLE / DEADLINE_EXCEEDED | 标注不可用/超时 | 写入状态未知时 reconcile，不盲重试 |
| SCHEMA_INVALID / STALE_GENERATION | 拒绝畸形或过期调用 | 重新读取 capability/plan，不重放旧批准 |

Provider 是归档事务唯一 owner。operation_id 绑定 schema、subject、kind、内容 hash 与规范化参数；同 operation 重试幂等，不以新标题/时间生成新操作掩盖未知结果。路线和授权摘要用于提交前一致性验证；generation 隔离新旧绑定，绑定迁移不改变已有候选的归属。提交截止前才允许取消；提交中取消/进程退出按未知结果对账，不声称取消成功且未落盘。

| Owner | State/Event | Resource | Termination/retry | Invariant/verification |
| --- | --- | --- | --- | --- |
| Provider | prepared/apply | 参数快照、目标、expected digest | 漂移拒绝，重新 plan | proposal、授权、目标一致 |
| Provider | committing/concurrent write | 事务锁、正文、registry、索引 | 最多 2 次同操作冲突重试，重查 generation | 不覆盖无关 dirty；不新增重复候选 |
| Provider | verified/replay | operation、persisted hash | 回读一致则 ALREADY_ARCHIVED | 稳定 item_id、subject、内容 |
| Provider | rejected/deny | 无提交资源 | 不执行，不更换身份重试 | 明确 persisted=false 或未知，不能假设 |
| Provider | committing/timeout/cancel/exit | 可能已经提交的事务 | UNKNOWN，先 reconcile | 迟到结果按 operation 与 generation 对账 |
| Provider | conflict/readback drift | 旧目标及当前版本 | 返回 CONFLICT，需要 review | 不补造成功，不复制第二份正文 |

性能建议初值：resolve p95 小于 200ms、warm context p95 小于 1s，read deadline 3s、archive deadline 10s；实测后冻结。预检不 hash 全目录，来源捕获是显式按需操作。只读重试最多 1 次；未知写结果不自动重试。默认无遥测；启用时只存计数、reason 和摘要，不能存 query、正文或机器路径。跨系统不承诺 exactly-once。

## 8. 实施阶段、迁移与回滚

P0：版本化模型和路由接口；允许项目无 repo_refs；repositories 按 identity_kind 条件要求真实 remote；普通目录使用 source/workspace，不进入仓库表；保持现有 remote 项目 fixture 原结果。

P1：显式本机绑定与发现结果分开保存；最长匹配、最近 Git/项目边界及冲突检测；Provider 提供 register/bind/resolve dry-run；A123X 使用 integration 项目和 workspace，实际仓库分别可选关联。source_refs/evidence_profile 不伪造实际 HIL。

P2：context 分离执行主体、读 scope 与写资格；非 Git 来源证据和分组 authority；归档允许无 Git 已登记项目，增加 receipt v2 与现有 v1 兼容投影。优先完成这一步，已可解决大多数现场问题。

P3：经明确独立 host policy 才开启 unassigned 候选及 assign。默认禁用、不重用 shadow proposal 权限。待分配区能力不成为正常项目归档的前置依赖。

P4：移植现有本地 workspace：发现条目仍为 discovered，确证显式条目才转 explicit；不根据历史目录推断新项目；做 dry-run 对比后原子迁移、hash 回读、备份。为每个当前项目验证 remote/cwd/query/显式项目四条路径；schema/工具变更经过全仓门禁，Runtime 集成另走受管 source-to-live。

remote 身份存在跨 provider 同路径碰撞风险：当前规范化去掉 host；可另立 provider/namespace/repo 限定身份迁移，旧 remote key 在服务端明确映射，不静默重新归属。它属于独立受控迁移，P0 不顺带全量改写已有仓库身份。

回滚：每阶段 feature capability 可关闭，registry/bindings 按事务 before 版本恢复并核验 expected digest；正文不自动删除或降级，已创建无 Git 项目及新候选不得让旧客户端误认成功。格式升级完成后禁止降级成无法读取新身份的旧工具；采用明确最低 reader 版本或兼容 read-only 模式。保留 dirty 工作区与用户现场。

## 9. 验收矩阵与完成标准

| 用例 | 预期 |
| --- | --- |
| 无 Git、已绑定项目 | context resolved，项目检索，candidate archive VERIFIED，不执行 git init |
| Git 无 remote/无 HEAD | 根据 explicit binding 路由，commit=null，来源证明不过度声明 |
| 完全未知目录 | 通用 discovery 可用，项目归档拒绝；inbox 只有独立 policy 启用才可写 |
| cwd A、显式检索 B | B 检索成功，默认归档不静默改为 B |
| query 同时命中多个项目 | 返回分组 discovery，不清空可信 cwd，也不授予单一写目标 |
| 项目零命中 | zero-hit 与 route resolved 同时成立，无伪造项目事实 |
| 父子路径、foo/foobar、同根多绑定 | 最具体匹配；组件边界正确；同根冲突拒绝 |
| 已登记/未知嵌套 Git 根 | 已登记子项目优先；未知子仓拒绝自动继承 |
| symlink 越界、目录迁移、同名新目录 | 越界拒绝；旧绑定 stale；不自动认领 |
| 显式绑定后运行 discovery | 显式绑定原样保留；发现冲突可审查 |
| 本机多副本/多机器 | subject 稳定，binding/source 分开，设备路径不进长期正文 |
| 文件变化/捕获超预算 | unstable/partial，不产生精确源码已验证声明 |
| personal、未知 actor、秘密输入 | 不越权检索或写入，不以 policy owner 推断主体 |
| 并发提交、断点退出、超时后已提交 | 无重复候选；先 reconcile；结果真实 |
| 待分配候选 assign/replay/冲突 | 一份正文、稳定 item_id、目标验证、reviewing 不变 |
| v1/v2 老客户端、新 schema 未知字段 | 协商或拒绝，不能把 unassigned 当项目成功 |
| Provider unavailable、Runtime readonly 门禁 | 知识故障与 Runtime 本地 conformance 分开，不虚构缓存/构建证据 |

完成分层：模型/接口审查完成，定向单元与异常测试完成，registry/检索/事务全回归完成，真实无 Git/A123X/嵌套仓集成完成，运行时受管部署完成，真实使用记录完成，分别报告。设计归档成功不等于上述任一实现阶段完成。Runtime readonly 任务误要求 build/repo 的问题应单独审查正确模式的可信路由契约，不能通过伪造 build、降低真实实施门禁或借其他线程绕过。

## Review 与下一步

建议先冻结 P0-P2，完成 Git 无关的项目登记、显式绑定和检索/归档解耦；P3 待分配区为独立可选能力。实现前确认无 Git 项目登记 schema、subject authorization、visibility 默认值及新 receipt 的兼容策略。本文只形成 reviewing proposal，owner review、接口实现、迁移与部署仍待完成。
