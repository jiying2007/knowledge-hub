---
id: provider-xcrz-sigmastar-demo-9031f7f3cea33504c97a3408
title: v43：优化几何已可行，但实际语音保护阻止晋升
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9031f7f3cea33504c97a3408.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:9031f7f3cea33504c97a34083cf4fc9a8ce2e5e7fd6d4ea6b9310143f555ff64
  source_sha256: 321614cc4ec1fdd8bd50117ca1f937795e5100417685c3cad340de8b882dfa47
  temporary_source_retained: false
review_after: '2027-01-09'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- debug-record
validation_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9031f7f3cea33504c97a3408.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/provider-xcrz-sigmastar-demo-9031f7f3cea33504c97a3408.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-11'
updated_at: '2026-10-11'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-11'
manual_validation_pending: true
summary_zh: v41完整收益目标在184例固定切线几何下未建立严格可行性。 依照用户允许的次级候选目标，v42新增显式optimization资格：每组1%研究收益加储备， 完整0.5dB/组验收和全部原实际语音/target/far/削顶/AGC保护保持独立。
  优化拟合Phase I严格可行、slack -0.07018513831060269；首次主求解有一个阶段128步未收敛， 全部流程按不合格保留，没有header，不能用后八阶段收敛替代全流程。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: xcrz-sigmastar-demo
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 9031f7f3cea33504c97a34083cf4fc9a8ce2e5e7fd6d4ea6b9310143f555ff64
---

# v43：优化几何已可行，但实际语音保护阻止晋升

v41完整收益目标在184例固定切线几何下未建立严格可行性。
依照用户允许的次级候选目标，v42新增显式optimization资格：每组1%研究收益加储备，
完整0.5dB/组验收和全部原实际语音/target/far/削顶/AGC保护保持独立。
优化拟合Phase I严格可行、slack -0.07018513831060269；首次主求解有一个阶段128步未收敛，
全部流程按不合格保留，没有header，不能用后八阶段收敛替代全流程。

v43仅将该优化模式的有界Newton步数提高为512，原收敛条件、几何、参数和开发数据不变。
重跑全部阶段收敛及量化保护通过，拟合far mean 0.416460757081667dB，
输出模型SHA 4a81ac341a59f7c4e65ae738411fcd4e5b9d4246fa641c7d9058d1c16dc76c45。
这仅为优化拟合资格，不是完整收益或实际整数PCM资格。

实际candidate/control/native observer编译成功，独立C合同在ASAN/UBSAN通过，
检查integer basis、echo/mic FIFO、无参考、Reset、VOICE和AGC状态。
原静态库未整体ASAN插桩；不能由该合同推导原生库全部无内存问题。
candidate SHA18d7abaf009e3ffaa834c4f8533ac5011da6d526950c17c803bca6583e78f2c0；
control SHA368260fbf9e8eeeb14931af5c33c429dc09cbba46c27d246f2f8872bccdb2c56；
native SHA f476e36597993ff6460d4c446b6805051b8736a8e94be7fbb356d5265e734b4b；
contract SHA0a72d0d805b5a73f397f69d5fdd8df0d828c486c48aa4b4770015e797d4327ad。

全部232例/11组实际C评价完成。精确PCM复核只扩展到32开发例及两组失败48例，
共80例；没有宣称全部232例精确PCM都已完成。
development24精确mean far +0.5046603297886113dB，全部原门禁通过；
development8 mean +0.45729789183958935dB，语音保护通过但完整收益门禁未过。
旧v27的24例精确DT最差-0.24213110806436777dB、target最差-0.2172996966088916dB；
v40已暴露24例精确DT最差-0.19487133232719245dB、target最差-0.2406817367716778dB。
这两组超出原DT -0.1dB/target -0.2dB保护，明确拒绝v43，不能以far均值更高取代人声保护。
新v42的24例继续未评分，不用它调参或证明失败方案通过。

137项Python回归全部通过，无skip；另一次全量运行的阶段probe路径写错，
一次启用了未编译weight trace的可选断言，修正调用环境后通过，未修改测试阈值或断言。
164项非tests原生源码对冻结v20 build identity无漂移，diff --check通过。
没有生产库/app/设备/上层reader/订阅/lease、发布或Git提交变更。
当前安全候选仍是v39小幅优化，不是完整解决或全局最优。

随后显式将两组已暴露失败48例纳入232开发；旧默认184及旧入口保持原允许集。
两个新增组的PCMC38映射均已通过并绑定冻结v37实际指标，232合并正在进行。
新232模型采用独立kind v44，保留所有原保护和固定优化目标；见PLAN-v44.md。
新的speaker/clip分离24例继续严格排除fit，NN预训练独立性未知。
