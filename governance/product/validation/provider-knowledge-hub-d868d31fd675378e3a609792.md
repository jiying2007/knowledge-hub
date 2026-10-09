---
id: provider-knowledge-hub-d868d31fd675378e3a609792
title: Knowledge Hub 第四轮审查与迭代
kind: validation
domain: governance
path: governance/product/validation/provider-knowledge-hub-d868d31fd675378e3a609792.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:d868d31fd675378e3a60979261a09d8515ec31cdca088886289a9ec735b06cc3
  source_sha256: 5099ba7a7693e541c69b56bc7ec3b811885fd99bbadc027eded91565b592f019
  temporary_source_retained: false
review_after: '2027-01-04'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- governance/product/validation/provider-knowledge-hub-d868d31fd675378e3a609792.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/validation/provider-knowledge-hub-d868d31fd675378e3a609792.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-06'
updated_at: '2026-10-06'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-06'
manual_validation_pending: true
summary_zh: 2026-10-06。本轮核对既有dirty工作区，审查检索与评估、恢复与复核运营、工程验收链，并核验官方资料；不是逐行人工全仓审计。保留此前改动与其他会话候选。owner批准、active提升和生产资格独立。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- Knowledge Hub 第四轮审查与迭代
related:
- indexes/obsidian-home.md
---

# Knowledge Hub 第四轮审查与迭代

2026-10-06。本轮核对既有dirty工作区，审查检索与评估、恢复与复核运营、工程验收链，并核验官方资料；不是逐行人工全仓审计。保留此前改动与其他会话候选。owner批准、active提升和生产资格独立。

## 落地

1. 检索禁止命中和无答案负例失败单独阻断；案例身份/类型有界且唯一；ID/path相关性按canonical文档去重；排名正例与负例拒绝指标分母分列。
2. 核真完整相关摘要弱于局部模糊标题的合成反例，增加受限exact-summary相关性信号，保持精确标题优先、泛词/body-only负对照、候选与authority门禁。
3. 本机同plan执行互斥；重复journal阶段重新确认耐久性；复核stock/pending读写同校验，损坏或未清pending明确needs-review。
4. 超时清理后保留有界输出；coverage只对明确数据错且实际测试已通过的情况有界恢复，超时/负信号/低覆盖/未知不重采；所有attempt结构事实优先。
5. 嵌套回归跳过单列delegated，产品消费者要求显式真实完整执行；预检使用工程实际解释器，CI验证其PATH身份，未放宽transport。

## 独立证据与负结果

交叉独立review：检索由恢复作者审，恢复由工程作者审，工程/Root超时/docs由检索作者审；三组Spec/Quality通过，无open major。coverage分类MAJOR-ENG-1通过六类独立反例关闭。新解释器预检小修复独立增量复验另行记录。

完整工程第一次在6155源码FAIL，Root调用环境未让PATH选择同一绝对venv解释器，真实CI拒64，11项失败、2项通过，未盲重试。完整失败报告及独立对象快照保留，host正文未保留。修正明确venv PATH并补实际解释器预检，不改规则或阈值。

最新冻结源码：ec50e259f13c560a1fe6cdfeb9f48890b0c6d6e881ab665971a8a890e507b49e。
完整工程在允许loopback socket与DNS的验证环境真实PASS，13/13checks，errors0；父pytest PASS159.743秒；full regression133/133真实执行PASS471.901秒、delegated0、full_regression_completed=true；包级覆盖78%（33109 statements/7440misses），原阈值75%，全部attempt1。完整报告SHA=8e51fcf82fbf44fbe43b4444ae720642b8c33fb29f4d9113f73f7e08a5f4710e；manifest SHA=352cfc78c1d6ec52d4667d89c4c737414b85d2ae19444333fa75cfbbcfb3a725；SBOM SHA=894fc5a4012fb7fb0b88889f24920e0f7fe96c4499f3eea4b3269567f87facd0。

该结果认证ec50冻结快照；source/candidate前后unchanged=true，host match=true。运行期间live变为c70d845117f54ed32b9c8df119b8dfe06f674eefdc29e1d0ba97cac1de654666：逐文件diff仅9个registry/index文件及另一会话新Provider候选，未变本轮代码。live metadata另行检查，不以旧整树QA认证新数据。

新12例第一次评估实际FAIL/exit1，hit=.6667、MRR=.5556、NDCG=.5466、authority=.5556；9正例中5例top-k命中、无答案3/3正确拒绝；forbidden0、安全完整性PASS，raw/shadow均FAIL。失败类别为目录权威、第二产品底座、私有技能分发及音频采集指南。source前后ec50不变；不改gold/规则/阈值，不将不同新旧问题集数值直接视为回归或提升。样本由未参与评分调优者仅据curated registry+README设计、未预评估；cases SHA=a84f608712923e6b3586e411d27a5c9aa0c787b92cc1cfc1f133065c4a381d92。

第二次sandbox完整工程9/13通过，4失败为pytest socket EPERM、3条fullreg失败、依赖/SBOM DNS。确认的直接socket测试与依赖/SBOM在工具许可的沙箱外单项复验通过，随后同冻结源码新环境一次完整验证全部通过；保留两个原FAIL报告，不拼接单项PASS为完整PASS。

原实施Runtime goal task-48637ee3a8d16072d1a85af4达到retry2后final实际exit3，保留未完成/耗尽历史；证据采集任务亦保留其未完成拆分历史。新的环境验证记录任务只一次完整机器验证及Provider记录，不再改源码/调参/改gold或full重试。其后续Runtime PASS不能洗旧目标，也不代表检索质量或生产资格。

## 外部依据

SQLite FTS5列权重：https://www.sqlite.org/fts5.html；Stanford开发/测试分离：https://nlp.stanford.edu/IR-book/html/htmledition/information-retrieval-system-evaluation-1.html；Python超时输出：https://docs.python.org/3/library/subprocess.html；Linux执行锁：https://man7.org/linux/man-pages/man2/flock.2.html。仅作为设计依据，未引入第三方运行资产或依赖。

## 边界

锁仅本机同plan，不代表跨主机exactly-once；AI代码审查不替代owner批准；合成反例与独立人工构造问题不替代真实生产检索。旧/新指标分母变化，不能直接宣称生产效果提升。未写memory、源项目、实时运行资产或远端Git。
