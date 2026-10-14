---
aliases:
- Knowledge Hub 恢复安全与自然问句检索优化验证
related:
- indexes/obsidian-home.md
id: provider-knowledge-hub-fe3802e55deaf44d2a249146
title: Knowledge Hub 恢复安全与自然问句检索优化验证
kind: validation
domain: governance
path: governance/product/validation/provider-knowledge-hub-fe3802e55deaf44d2a249146.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:fe3802e55deaf44d2a2491461996be43c00d1b14b0520bf68337459c17bc256d
  source_sha256: 815b67da5c0880b337d012fb07a036297af08d0d022e84efdc1ad0761ff7c94b
  temporary_source_retained: false
review_after: '2027-01-07'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- governance/product/validation/provider-knowledge-hub-fe3802e55deaf44d2a249146.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/validation/provider-knowledge-hub-fe3802e55deaf44d2a249146.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-09'
updated_at: '2026-10-09'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-09'
manual_validation_pending: true
summary_zh: 本记录为 reviewing 验证候选。工程、检索、恢复、Provider 持久化、Owner 和生产资格分别验收；不授权提升 active 或正式发布。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: knowledge-hub
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: fe3802e55deaf44d2a2491461996be43c00d1b14b0520bf68337459c17bc256d
---

# Knowledge Hub 恢复安全与自然问句检索优化验证

本记录为 reviewing 验证候选。工程、检索、恢复、Provider 持久化、Owner 和生产资格分别验收；不授权提升 active 或正式发布。

## 实现与边界

修复缺少 before/after hash 的历史事务审计和回滚：状态保持 unknown，recoverable=false，实际回滚拒绝覆盖后续用户字节。六种缺失 hash 与路径标记组合均有负测试。

普通介绍、读取和位置问句按相关性排序；仅明确规范问句前置通用规范，shared comparison 分支保持原契约。清理问题中的读取动作，保留注册 alias、浏览器名词、语料正文和限定词。既有多语言同义词单元参与分词，但含明确中文主体头的片段不进行新增的同义词内部拆分，未知项目、设备、板卡和仓库继续拒绝。

匹配器先检查字面词是否存在，再执行原边界正则。独立 19696 项新旧匹配对照全部一致，未改同义词、可见性、显式主体约束或质量阈值。实际两问句 profile 中正则 search 调用从 9673 次降为 858 次；这只证明优化路径，不代替整体性能门禁。

候选恢复演练的完整 pytest 使用与工程门禁一致的 300 秒预算，其他检查仍默认 180 秒。超时返回结构化失败，不签成功 Parent Unit 回执。README 说明解释器选择、源码与宿主绑定、历史恢复身份及 Owner 边界。

回归临时 fixture 在根排除本机私有目录、运行资产和工程派生产物，保留项目源码与正文；常规缓存不进入各层 fixture。日期契约用例使用既有固定递归保护调用语法，继续执行日期、过期警告和状态断言，显式要求嵌套单元测试 exit77 delegated-unverified。该用例只验日期契约，完整工程另执行完整 pytest、全量回归和覆盖率门禁。CI transport allowlist 未修改。实际 CI 日期用例 PASS 33.217 秒。

## 源码与验证

基线 HEAD：d4b00e00df0c7a1f4c418614e383e9ec04616a10。最终冻结源码签名：3e18fb2e5ab0a651205a3a06939f2bd9f49bf6a031a8faa6832f4e95198145f9。保留原有工作区改动，未自动 commit、push、merge、改 memory 或源项目。

完整工程于 2026-10-09 12:34:43 UTC PASS，13/13 checks、error_count=0，所有正式检查 attempt_count=1。实际 Python 3.11.16；完整 pytest PASS 199.448 秒（同源码收集 1975 tests）；full regression 实际执行 133/133 PASS、delegated_result_count=0、full_regression_completed=true，335.745 秒；coverage 78%，阈值 75%。ruff、mypy、Bandit 中风险中置信度门禁、构建、知识结构、默认检索基准、依赖审计和 SBOM 全部 PASS。

源码前后签名与 live 相同，host inputs match=true、live_matches_snapshot=true。完整报告 SHA256：4d86ef97875a3bb72cdb5ed207fe98171358ee333e5b94282fcdd03eba0ac675。wheel SHA256：759863b80bee951d23bda599db28cc12f36fe4c19a7e44776c1b5a5e93f81963；sdist SHA256：fe22cef95dd7e455a14cefdeeb5c0533a2be53cee8b5d4e9eaf9e13200d7b5fe。上述结果覆盖登记前 3e18fb2 冻结树与所记录解释器、专用内存临时盘条件；Provider 登记后 registry/index 输入变化另行验证，不直接继承该全仓资格。

独立源码审查的 spec 与 quality 均 PASS；复审曾发现读取动作遗漏和未知中文主体约束回退，修复后重新审查，无未闭合 major。恢复超时和正则预筛选亦分别通过独立复审。

首次独立 12 例 FAIL 已保留：命中率 0.6667、MRR 0.5、NDCG 0.5262。曝光后该组转为 development-regression，不再称未见集。修复后的同组为 PASS，命中率 1、MRR 0.95、NDCG 0.9631、authority recall 1、p95 349.77ms，两例未知主体均正确拒绝。该结果不作为独立泛化资格。

第二组独立冻结 6 例首测 PASS：4 有答案、2 显式未知主体拒绝；命中率 1、MRR 0.875、NDCG 0.9077、authority recall 1、p95 474.62ms。禁止、控制文件、未登记和重复结果为 0，raw 与 shadow 都 PASS。并发与 scale 未在该自定义集测量，production_qualification=false。

第二组 dataset SHA256：a468bf9160ad3a2c0e9fe973e498b16fa93a74a3f0101d1909a3efa27eca9a64；cases SHA256：d3ae801d40f66b752049d710700368583c91c5e73621e30069ef539e12b55231；首测结果 SHA256：85d88544b6e16a988696cf9946e110b484eca86f54bb8ab8fd5da460132b44de。冻结前未搜索，首测期间源码未变化，独立审查者回读验证了身份与结果。

第二组首测的全仓签名为 c5c0ff8b1a968731a182271aa9be60cd9a204bab87442ad48cf73f8f73ce4f81。其后变更仅回归 harness 和工具说明，检索组件未变；首测报告继续绑定原签名，不重标为最终全仓工程资格。

历史负结果继续保留：系统 Python 3.8 性能失败不由 Python 3.11 PASS 覆盖；旧恢复演练在 180 秒超时；c5c0 源码首次完整工程有 pytest 300 秒超时、full regression 600 秒超时、benchmark 性能失败与覆盖率 34% 低于 75% 四项 FAIL。失败报告 SHA256：edaefdfe777fe2a9aea68fff6d5b84016da71897e8a8c108e8ac8c72602fc140。覆盖率可能受超时造成的采集不完整影响，原报告仍为失败。后续为同源码、无其他本线程重验证并发的受控复验，未提高工程超时或质量阈值，不能称自动 transient retry。

同 c5c0 源码的第二份工程仍 FAIL：完整 pytest 和 benchmark PASS，full regression 600 秒超时、覆盖率 72%。诊断观察器执行 133 结果，有 3 FAIL：私有目录 ghost-copy，以及 live 诊断没有 fresh parent unit 引起的两项门禁失败；诊断装配不能冒充正式 snapshot 门禁。日期用例自身通过但耗时 250.403 秒，包含冗余整套 pytest。修复 fixture 复制和日期验证范围后，f7f2124 工程 12/13 PASS，完整 pytest 236.971 秒、覆盖率 78%、full regression 133 结果在 305.61 秒执行，唯一失败是新增 rtk env 被 CI transport 拒绝。该负结果 SHA256：1faf3cf61a4048d67cf6d8ea118134036234d9e1e077eaa45f1a1c790d8e6fa2。已改用既有固定 transport grammar，未放宽权限或提高正式 300/600 秒、75% 门槛。

3e18fb2 首次完整工程因根分区 ENOSPC 中断，连失败副本都未创建；旧工程缓存不能当作该次结果。实际可用空间约 119MB，inodes 充足。错误输出 SHA256：f7b873e35fed3ede954a65f1fbd73fdedb0d80b49bcf121323738c1372d6d69e。随后经明确沙箱批准，在另一本地文件系统建立 0700 专用临时目录，完整工程和恢复副本使用该目录；源码、超时和质量阈值不变，没有清理旧现场数据。完整报告保留实际环境与身份，性能结论不扩展到不同解释器、磁盘或宿主条件。

该源码在专用磁盘目录的完整验证仍 FAIL：pytest 接近结束时超出 300 秒，没有成功 Parent Unit 回执；两个要求该回执的回归门禁随之失败，全量回归实际执行 133 结果、335.005 秒；不完整覆盖率 40% 不能作为完整覆盖率。检索基准、日期契约和其他检查通过。该报告 SHA256：7b9fe5e37be6903fe5bdb47f3452f9964a520378a2ab9bfc95e8f874c0d22e7f。随后使用另行批准的专用内存临时目录进行受控验证，未改源码或门槛。上一轮已结束的 197MB pytest 临时副本经批准完整搬移，回读代码 hash 一致；这是保留内容的搬移，不是删除历史失败或用户数据。

真实 candidate 恢复演练于 2026-10-09 12:37:53 UTC PASS：2030 个文件复制校验，11/11 checks PASS，missing=0、symlinks=0、hash_mismatch=0，network_used=false；完整 pytest 实际 PASS 125.014 秒，每项 attempt_count=1。恢复报告 SHA256：909d4eba2ef378c0df8984c9ed5460436c539dce5a3e7e4b80278d40dd0f0bac。source_mode=candidate，签名与上述冻结树相同；scratch Git 只供离线验证，remote_checkout、remote_published_ref 与 offsite 均 false。

正式 product/full 门禁于 2026-10-09 12:39:44 UTC 返回 NEEDS_REVIEW、terminal=false、exit_code=0，19/19 hard checks true，platform PASS。工程与全量回归使用新鲜且签名匹配的实际 PASS 证据。剩余 5 项均独立披露：Owner 与真实项目证据、clean committed HEAD 本地交付、远端发布、异地恢复、实际长期采用。32 项目结构 ready，真实证据 ready 6、pending 26；内容人工队列 210。此门禁的 exit0 表示有可读结果，不表示产品终态成熟。

## 运营与未闭合资格

已按实际日期准备过期内容、来源和候选的有界 Owner 复核包；不自动延后 review_after，不代签。2026-10-09 登记前机器包为 report-only、error_count=0：items_total=627、stale_items=302、near_due_items=248，18 个来源均过期，detail_row_count=568；每批 10 条，3 个 registry 声明 owner 分组。该宽口径包含多个生命周期状态，不能与 active-only 过期统计混用；owner_gate_open_count=0 不代表内容已获人工批准。项目真实证据、人工内容决定、clean committed HEAD 交付、远端发布、异地恢复、实际长期采用与 Obsidian GUI 观测分别保留待验；机器检查与源码审查不替代这些资格。

## 复用决定与回退

- delivery_goal：本地恢复安全、自然问句准入与排序、性能、工程和证据闭环。
- reusable_pattern：身份不完整时拒绝自动恢复；语法和主题单元不能擦除主体约束；严格等价预筛选减少无效扫描；负结果保留并按数据集调参历史分层。
- affected_asset：Knowledge Hub 本仓工具、测试与工具 README。
- promotion_candidate：false；do_not_promote_reason：本候选未完成内容 Owner 审阅，不授予团队发布或生产资格。
- next_task_friction_reduced：true；reduced_by：回归负例、独立冻结集、解释器与恢复预算说明。
- reduction_evidence：未知中文主体、缺 hash 回滚和真实超时均有可复跑负测试；19696 项匹配等价核验及实际 profile 支持预筛选路径。
- owner_review：独立 AI 源码审查 PASS，人工内容审阅 pending。
- rollback_path：仅反向应用本轮源码、测试和 README 的对应补丁，保留用户已有 registry、indexes、候选和未完成事务；Provider 候选回退另按完整内容身份与治理契约处理，不自动删除或提升。
- verification_evidence：上述源码、数据集、结果和报告 hash 及公开命令。raw log、完整会话、制品、设备标识和凭据不进入候选。

## 完成声明核对

claimant：本轮实现者；verifier：实际 CLI、冻结完整工程、恢复副本及独立源码审查。源码 review spec/quality PASS，无未闭合 major；旧独立首测 FAIL、工程 FAIL 和环境中断均保留。

| 适用检查 | 命令或方式 | 结果与退出码 | 验证层 |
| --- | --- | --- | --- |
| lint、类型、安全、构建、完整测试 | knowledge-engineering-check.sh --mode full | PASS，exit0，13 checks、1975 tests、133 regression、78% coverage | 登记前冻结源码 |
| 恢复与 smoke | knowledge-restore-drill.sh --source-mode candidate --as-of 2026-10-09 | PASS，exit0，11 checks | 本地候选恢复 |
| 正式产品门禁 | knowledge-final-gate.sh --regression-suite full --reuse-engineering-evidence --as-of 2026-10-09 | NEEDS_REVIEW，exit0，19 hard checks true，5 外部或交付缺口 | 领域成熟度 |
| 独立自然问句检索 | 第二组冻结 6 例首测 | PASS，exit0；绑定 c5c0 原始签名 | 检索组件 |
| 独立源码复审 | spec、quality、transport parity 只读核对 | PASS，无未闭合 major | 源码审查 |

完成范围限于上述实现与登记前验证。Provider 持久化只依据随后真实 ARCHIVED/ALREADY_ARCHIVED、persisted=true 和内容 hash 回读；登记改变 registry/index 后再次验当前输入，未完成该步前不扩展冻结树资格。人工内容批准、active 提升、SCM 发布和生产验收未完成，不声明产品全面终态。rollback 只对本轮对应补丁操作，保护原有 dirty；恢复 journal 缺 identity 时保持 unknown/conflict、不自动覆盖。

本次未修改运行时模型、权限、trust、技能资产、connector 或 UI；Trace Eval、source-to-live 和设备/HIL 验收不适用。Runtime Execution Policy 仅验证本地 conformance，不替代上述领域验收。
