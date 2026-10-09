---
id: provider-knowledge-hub-d07893a6a191b3752a3b832c
title: Knowledge Hub 第六轮全面迭代验证记录
kind: validation
domain: governance
path: governance/product/validation/provider-knowledge-hub-d07893a6a191b3752a3b832c.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:d07893a6a191b3752a3b832c896fcb088b3f305f8107bf4cf8f7e936e1c329e2
  source_sha256: 28e24aa8bd25cc1379de554896516e950fa0294982bd7ab29b10a2c82adeb5e4
  temporary_source_retained: false
review_after: '2027-01-05'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- governance/product/validation/provider-knowledge-hub-d07893a6a191b3752a3b832c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/validation/provider-knowledge-hub-d07893a6a191b3752a3b832c.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-07'
updated_at: '2026-10-07'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-07'
manual_validation_pending: true
summary_zh: 2026-10-07。用户授权全面本地审查、外部搜索与源码迭代；本轮范围为 Hub 工具、测试与文档。保留既有未提交改动。claimant=Codex；verifier=独立非作者审查与隔离快照工程验证。源码验收已通过，检索泛化和生产资格仍未闭环；不将
  reviewing 记录提升为 active。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Knowledge Hub 第六轮全面迭代验证记录
related:
- indexes/obsidian-home.md
---

# Knowledge Hub 第六轮全面迭代验证记录

2026-10-07。用户授权全面本地审查、外部搜索与源码迭代；本轮范围为 Hub 工具、测试与文档。保留既有未提交改动。claimant=Codex；verifier=独立非作者审查与隔离快照工程验证。源码验收已通过，检索泛化和生产资格仍未闭环；不将 reviewing 记录提升为 active。

## 已落地

- 已登记项目的通用比较可召回团队通用 standard/architecture/runbook；显式过滤先行，项目范围、其他项目、个人材料及不可检索内容的约束保留。未知比较操作数及并列操作数遗漏经独立反例修复，有界语法矩阵覆盖，并明确不承诺任意自然语言解析。
- 查询词变体与正则每次查询编译一次，文档内匹配复用；项目域约束提前执行。两候选通道使用同一 SQLite 快照，保留各自 cutoff、顺序与预算，唯一正文读取一次。固定32占位符SQL仍绑定参数，消除B608扫描歧义，不声称修复原本不存在的SQL注入。
- owner-ready建议要求明确正向决定、accepted内容、当前正文hash、有效复核期及可确认的verified证据；拒绝、陈旧、未知和未验证声明不能ready。正文首读与确认读计入同一共享预算，超限真实overflow，不虚报metadata-ready。
- 进程deadline覆盖父进程与管道EOF；非阻塞采集无drain线程，超时保留有界输出并关闭自有FD。仅清理自有进程组；外部reaper导致ChildProcessError时不再signal失去身份保证的PGID。Linux waitid/WNOWAIT契约和不支持外部并发reaper已记录。
- 产品门禁5个实际命令的超时转为exit124/failed-timeout/incomplete，保留原45/60/60/180/20秒限制、非命令及非超时异常继续暴露，unit不能伪造PASS/reuse。回归增加有界stderr；仅预算单测显式启用临时fixture的telemetry，生产及回归隐私模式保留。
- generation与local-metrics schema精确同步到v3；旧v1/v2保留usage历史，不获得v3性能资格。

## 新鲜验证

最终源码身份6aea4ab45ecbe16fd05b314783134a35ed54fe0401cc9a8c648666430aeb2272，HEAD f5d172c7deb59af4e305ce02390978b880354b1c，2001个输入包含已有dirty overlay。第二次隔离快照工程13/13 PASS、0errors；完整pytest/coverage207.532秒，完整回归133/133实际执行PASS、delegated0、499.149秒，覆盖78%（33857 statements/7495miss，原阈75）。source/live/host与测试前后身份一致。Ruff、mypy92源码、Bandit、build、knowledge check、既有benchmark、依赖审计与SBOM通过。

完整工程报告SHA5d50b4d42087584f05c3921241da7cbd5ae73fca85833f7e7ffed552eeb12f06；manifest SHA246a7a83abc630f6126fac7c080285cce70a0a8ca4a7c73cb009cb7516581866；SBOM SHA08e3f0d2a1867d7ec27dab2f0cca9e24c9aa4e393102fb4b7ecbe9d6912adb12。

独立检索源码152tests PASS（含36比较并列负矩阵）、治理82tests PASS、进程ownership独立反例PASS、门禁增量112tests PASS；各审查openmajor=0。独立review报告SHA依次为0632ede5ef3c8c305239d4ea3f5b9607df83b2d45b58a91ff8578db465eb0140、a3e3235076f516d15551ad2e01200aa8214564a6570c6e1c35726063f12c167f、79bedb4d0a3ea0c1c634159fc9ae4e9de77b905301cc99d64a64d0399fe82265、c51fa7f5e21fb9956f4456d9d0b522c16d485a1bd043ac053af0f6f2682e1ca7。

## 保留失败与资格边界

首次full source4090f08e7f06bf3d9b367e1f7ebce1f314440e6b263e31758253b4595a78ccaa真实11/13FAIL：Bandit固定placeholder表达式以及回归as-of调用无JSON。原报告SHA6f98c7be687560e90eb4efe523ce88f355f86a2ce5688c7907e44f67b84e85cb及private replay保留。旧快照单项复跑PASS/有效JSON不改写旧失败。原空JSON底层原因仍unknown；独立注入核真future timeout传播，与原失败归因分开。

新20例非调优作者依据登记正文冻结（16正例/4负例），首测source1434d186f221c1d643607802d3e5fae81dbf488784cf6e4865d8e1c18081f934前后一致；dataset SHA1b0958c51550c44b9cb57379b66b88fe95d3d28d4ff41406373165a57c33bc04，cases SHA80ec972c73850f865bb0dcc725491f5c34b07bd7bb1a952bfa606d3a80846bd3。quality FAIL/exit1：hit.7、MRR.625、NDCG.6008、authority recall.625；4负例全正确，forbidden0/完整性PASS。p95=225.54ms/max356.64ms，性能阈500ms；并发/规模探针未执行。raw/shadow均FAIL，不据修后复跑冒充未曝光验收。最终策略没有另一套未曝光泛化证据，生产资格不成立。

已曝光18开发问的一次同机warm对照总耗时3902.32→3122.41ms，降低19.99%；个别宽泛目录问仍603.72ms。该对照发生在后续边界补丁前，不是最终策略SLA或跨数据集P95提升证明，原gold/expected/阈值均未修改。

后续需改进一般中文治理问法、概念与主体区分及比较/否定表达的召回，并另建未曝光验收集；Owner适用性决定、active提升与生产采用仍需独立真实证据。未关闭Owner gate、续期旧条目、写memory、改源项目或发布运行资产；本轮未产生新Git提交/推送/合并。Provider及Runtime只按实际后续回执报告，不预先声称记录成功。

## 官方设计证据

Elastic query/filter context：https://www.elastic.co/docs/reference/query-languages/query-dsl/query-filter-context 。参考相关性与必须满足的结构过滤分离。
SQLite FTS5：https://www.sqlite.org/fts5.html 。候选与排序成本以本地profile验证，不据文档擅改FTS权重。
Python cProfile：https://docs.python.org/3/library/profile.html 。profile用于找CPU热点，无profile墙钟用于性能合同。外部内容只用于设计核验。
