---
id: provider-llm-agent-1e0955b8405e311ca5dc1a58
title: ADK 8.0.4 与 llm_agent 归档资源治理迭代
kind: validation
domain: projects/llm-agent
path: projects/llm-agent/validation/provider-llm-agent-1e0955b8405e311ca5dc1a58.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:1e0955b8405e311ca5dc1a586bea8c90ac035563245248ff9ad0201de4605075
  source_sha256: 02b8c7acdf4dcd55fa89a48c05c79a3ec975d17b7d7291f912729167ca3c23c3
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
- projects/llm-agent/validation/provider-llm-agent-1e0955b8405e311ca5dc1a58.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/llm-agent/validation/provider-llm-agent-1e0955b8405e311ca5dc1a58.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-07'
updated_at: '2026-10-07'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-07'
manual_validation_pending: true
summary_zh: 状态：reviewing；不声明产品资格或运行资产升级。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- ADK 8.0.4 与 llm_agent 归档资源治理迭代
related:
- projects/llm-agent/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# ADK 8.0.4 与 llm_agent 归档资源治理迭代

状态：reviewing；不声明产品资格或运行资产升级。

内部取证：8.0.3 verifier 可在拒绝缺少关键JSON之前缓存12000个零载荷成员；74507字节压缩输入不能证明无资源风险。Python官方tarfile文档明确过滤器不能替代DoS防护；CodeQL官方py/tarslip要求验证成员输出路径。

落地：64MiB regular compressed snapshot、128MiB decoded、8192成员、单成员32MiB、4096字节名称；metadata/header链/PAX键单独限额，清除TarInfo缓存并完整验证gzip EOF/CRC。摘要、真实rehearsal提取及publish上传绑定同一snapshot；CLI保留叶节点边界。CodeQL首次高告警后改为预检所有成员，再显式读取普通文件并独占创建，保留执行位但屏蔽特殊位；不承诺一般tar元数据保真、同UID/受攻击父目录安全或精确RSS/墙钟收益。

来源：ADK PR180已合并d5c4795c77ec4e51f015f39a8da14f0d6b5b8975；Main CI37609032703九job成功，release37609624802成功；immutable v8.0.4/id405658156，tagd166d3fa276ae999bdd23849d9ef33898f33d297指向同commit。实际公开归档SHA256 f7d361371b67447a462e9c75a87652eb57fee354c7167e6d6e8e095b5147d699匹配官方API、新signed evidence及release contract；固定可信根/官方workflow/issuer验签Verified OK。

消费：llm_agent PR189已合并aaa7d43b117a8f8e216a7ff3ad5ee528398370ce；六来源原子更新及三项真实入口consumer测试。ADK三Python各98/98、30/30及全部审计成功；22archive/14JSON通过。Root完整离线回归74/74通过，独立只读源码与最终验收PASS；quick49/52，dirty参考基线过期影响两个检查、历史M5 candidate mismatch影响第三个，保持阻塞。Root main CI另由最终SCM读回核验，不依据PR推断。

负结果：首次Root sandbox full7/6/1失败，实际_execute版本探针沙箱内交替空TimeoutError，沙箱外四次成功；执行器版本间无变化。升级后完整回归74/74，不改源码或timeout，不推具体OS/asyncio根因。ADK quick功能56/56但141/144s超过120s，正式8.0.3同镜像基线139s也超限，不放宽预算、不宣称提速。

保留：十个参考目录、独立Codex五dirty文件及journal，live8.0.2与冻结gitlink；本轮无需runtime正文更新，没有真实模型调用。source/current-evidence-historical、release_authorized=false保持；owner身份和active promotion未推断。下一优先项为quick耗时定位、真实参考基线复审、产品新证据，分阶段另验。

公开设计依据：https://docs.python.org/3/library/tarfile.html#hints-for-further-verification 、https://docs.python.org/3/library/gzip.html 、https://codeql.github.com/codeql-query-help/python/py-tarslip/ 。
