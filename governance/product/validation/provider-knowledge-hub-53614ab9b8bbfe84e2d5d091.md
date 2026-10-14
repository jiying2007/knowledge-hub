---
aliases:
- 证据缺口盘点与复核推进记录
related:
- indexes/obsidian-home.md
id: provider-knowledge-hub-53614ab9b8bbfe84e2d5d091
title: 证据缺口盘点与复核推进记录
kind: validation
domain: governance
path: governance/product/validation/provider-knowledge-hub-53614ab9b8bbfe84e2d5d091.md
scope: team-general
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: provider-policy-sha256:a295759999c3c3c2594752350565bbde6af74808af32b9272604f53a36f82736;operation:53614ab9b8bbfe84e2d5d09143829fcf04694300d02e1f1e647df93823366592
  source_sha256: c12a335e362943eb6befd20198d6702da78fd43cb59ab08f9a1269488e9ac510
  temporary_source_retained: false
review_after: '2027-01-08'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- governance/product/validation/provider-knowledge-hub-53614ab9b8bbfe84e2d5d091.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- governance/product/validation/provider-knowledge-hub-53614ab9b8bbfe84e2d5d091.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-10'
updated_at: '2026-10-10'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-10'
manual_validation_pending: true
summary_zh: 日期：2026-10-10。范围：Knowledge Hub 本地证据发现、reviewing 就绪页导航与 AI 语义预审。状态：reviewing 候选；不代表 Owner 签收、active 提升、项目发布或设备通过。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  id: knowledge-hub
  type: project
created_subject_ref: *id001
principal_id: null
provider_operation_id: 53614ab9b8bbfe84e2d5d09143829fcf04694300d02e1f1e647df93823366592
---

# 证据缺口盘点与复核推进记录

日期：2026-10-10。范围：Knowledge Hub 本地证据发现、reviewing 就绪页导航与 AI 语义预审。状态：reviewing 候选；不代表 Owner 签收、active 提升、项目发布或设备通过。

## 结果与计数口径

本轮 registry 快照为 643 条，SHA256 `991cfa469911d1a3765e5dff6d030d1b2d1d55e5267fecf6a80c7887a73d2d56`。独立重算 32 个项目合同，其中 6 个就绪、26 个待补。缺失字段分别为设备 20、回滚 25、发布 21、制品 19、来源 1、验证 1、成员依赖 1；同一项目可以缺多个字段，不能将字段计数相加当项目数。

本轮 3 份 reviewing 就绪页增加 21 行历史证据导航；未改变合同、Owner、人工复核字段、生命周期或资格。9 条治理规范已实际进行 AI 语义预审，8 条建议保留、1 条提出具体文字建议、1 条因导出边界未进入语义正文审阅。结构回读 PASS 只证明 hash、唯一锚点和响应格式绑定，不认证建议语义或模型身份。真实证据绑定 0、人工签收 0、待办关闭 0。

AI 内容缺少复核三字段的本轮快照为 226 条。这是 `generated_by_ai` 且缺 `human_reviewed_by / human_reviewed_at / review_basis` 的口径，不是全部逾期任务或最终 live 数量；并发归档与本候选登记可能使其继续增长。

## 已落地导航与证据拒绝原因

- `projects/x5-rdk/validation/project-readiness.md`：引用原归属 `projects/firmware-toolchains/validation/2026-08-05-x5-v1.1.2-firmware-build.md` 与 `2026-08-06-x5-pre-board-readiness.md`。现有材料记载固定 manifest `9b1e8ef20c56304db60ce89159c4eaa0e057264f`、integration `135b1e8c93166ea2aca3dc686ddd69e8138666e0`、镜像哈希及主机构建；原文仍待复核，补录前须回读源仓不可变机器收据。跨项目引用按 X5 README 的历史来源边界，不迁移或复制正文，不自动认证 source/validation/artifact。
- `projects/llm-agent/validation/project-readiness.md`：标明原页 2026-07-17 的历史基线，引用 `adk-v3-1-rc3-release-closure-20260718.md`。该文 RC3 制品哈希和 39 项升级回滚属于 ADK 子仓；不能填入 llm-agent 根产品的制品、发布与回滚合同，也不能证明当前版本已复跑。
- `domains/codex/validation/project-readiness.md`：补 `provider-codex-8008d911326cf0c6cbb838fb.md` 导航。2026-10-06 的 source-to-live 与采用记录存在，但 live apply、备份或 clean managed state 不等于真实回滚演练，也不证明当前 live 状态。
- Firmware Release Tools 的 NAS 发布同步记录是历史 archive-only 来源，不能据此确认当前工具发布基线。
- MCU 已登记六个成员，不缺成员名单；`member_project_ids` 待补表示五个成员尚未 evidence-ready。应逐成员补证据，不能重写名单或提升聚合状态消项。

## 26 项具体推进清单

| 项目 | 当前缺失资格 | 可推进动作及验收输入 |
| --- | --- | --- |
| pcr02-ssc305 | 设备、回滚 | 对已登记制品补同版本目标板测试及实际回滚记录；局部性能 A/B 不替代发布验收 |
| xcrz-sigmastar-demo | 制品、设备、发布、回滚 | 绑定主仓/子仓 source lock、最终制品哈希、真实发布收据与同制品板级结果 |
| pcr02-api | 制品、设备、发布、回滚 | 核模块源码与最终消费者制品身份；不可直接借用主仓设备结论 |
| pcr02-app | 制品、设备、发布、回滚 | 核应用最终制品、发布身份、目标板与回滚记录 |
| pcr02-hdi | 制品、设备、发布、回滚 | 核 HDI ABI、最终链接身份及消费者设备验证 |
| pcr02-sensor | 制品、设备、发布、回滚 | 核独立子仓提交、最终制品及目标板验证 |
| pcr02-daemon | 制品、设备、发布、回滚 | 核消费者部署身份、真实运行与回滚记录 |
| pcr02-cli | 制品、设备、发布、回滚 | 核目标平台 CLI 制品、命令 smoke 与回滚记录 |
| pcr02-cmd-server | 制品、设备、发布、回滚 | 核最终服务制品、协议与目标环境结果 |
| pcr02-proto-c | 制品、设备、发布、回滚 | 核生成代码/协议版本与最终消费者制品及兼容性 |
| pcr02-wifi | 制品、设备、发布、回滚 | 核最终网络库与设备 Wi-Fi 行为及回滚 |
| pcr02-mp4 | 制品、设备、发布、回滚 | 核最终存储库、设备录像/封装结果及回滚 |
| app-ota | 制品、设备、发布、回滚 | 核升级包 source lock、保数据行为、升级与实际恢复结果 |
| app-product-test | 制品、设备、发布、回滚 | 核工装/应用版本、实际站点与产测终态 |
| app-tool | 制品、设备、发布、回滚 | 核工具消费者及目标运行环境，保留真实部署与回滚 |
| app-main | 制品、设备、发布、回滚 | 核主程序最终链接身份、设备行为与回滚 |
| mcu | 成员依赖就绪 | 保留六成员名单；firmware-release-tools、firmware-toolchains、gd32l235、hc32f072、mm32spin023c 未就绪 |
| gd32l235 | 设备、回滚 | 对已登记源码/制品补充同版本 MCU 实机与实际恢复结果 |
| hc32f072 | 设备、回滚 | 对已登记制品补充目标芯片/板实机与回滚结果 |
| mm32spin023c | 设备、回滚 | 对已登记制品补充目标芯片/板实机与回滚结果 |
| firmware-release-tools | 制品、发布、回滚 | 核工具自己的制品/版本/发布及失败恢复；固件 NAS 发布不等于工具发布 |
| firmware-toolchains | 发布、回滚 | 核对应工具链精确版本、权威分发身份、安装/恢复记录；本地下载哈希不代替发布方校验 |
| codex | 发布、回滚 | 回读对应版本真实发布及受管 rollback 演练；不得以 live apply 替代 |
| llm-agent | 制品、发布、回滚 | 核根产品消费者交付身份，ADK 子仓证据单列 |
| x5-rdk | 来源、验证、制品、设备、发布、回滚 | 优先回读已发现 X5 固定 manifest、构建收据与镜像；板级结果与实际恢复另补 |
| digital-worker | 制品、发布、回滚 | 已有 source/Actions 不足以证明可交付制品；补产品包、真实发布与恢复 |

清单是 AI 准备的验收输入建议，不授权写源项目、连接设备、发布或关闭 Owner gate。

## 一项治理修订建议

`governance/command-tooling-rules.md` 的“不让无人值守自动化执行 --apply”与当前 AGENTS 的低风险 Provider candidate-only 自动登记授权存在解释冲突。建议限定例外为：已有明确 candidate-only 授权、有效 Provider 策略、脱敏低风险结论、reviewing 状态；不扩展到生命周期、Owner、发布、删除、源项目或外部写。该 active 规范本轮未改，仍需 Owner 复核精确建议。

## 验证与下一步

2026-10-10 在 Hub 工作目录执行知识检查，修改前后均返回 exit 0、status pass、errors 为空。对应的稳定路径复跑命令为 `rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --as-of 2026-10-10`；此处将当时的仓库相对路径规范为绝对位置引用，不改变历史执行结果。历史 review_after 逾期警告保留，未自动延后。三文件 `git diff --check` 通过；既有 dirty 保留审计通过。此次仅文本导航维护，未重跑完整软件/设备/发布套件，不能沿用旧全量快照证明当前全部产品资格。

后续先接入已有不可变机器收据，再按项目/源码/制品身份核验；真实内容签收通过现有精确确认与受控消费入口进行。AI 可以持续发现、分流、读取允许的正文、形成修订和核验建议；人工字段、设备结果和发布/回滚资格不由 AI 编造。
