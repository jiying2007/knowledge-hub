---
id: pcr02-overseas-product-alignment-brief-20260903
title: PCR02 海外产品化协作对齐说明
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-09-03-pcr02-overseas-product-alignment-brief.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
related:
- projects/xcrz-sigmastar-demo/archive/reports/2026-09-03-pcr02-export-readiness-compliance-gap.md
source:
  type: sanitized-external-alignment-derivative
  from: 2026-09-03 PCR02 产品出海就绪度内部评估的脱敏协作版本
  temporary_source_retained: false
review_after: '2026-12-03'
review_status: partner-alignment-draft-pending-owner-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; collaboration brief only, not a certification claim, commercial commitment, or launch approval
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-09-03-pcr02-overseas-product-alignment-brief.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: sanitized-internal-alignment-draft-owner-review-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-09-03-pcr02-export-readiness-compliance-gap.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
tags:
- pcr02
- overseas
- product-alignment
- partner-brief
- compliance
- cybersecurity
- privacy
- validation
created_at: '2026-09-03'
updated_at: '2026-09-03'
captured_at: '2026-09-03'
last_verified: '2026-09-03'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-03'
manual_validation_pending: true
summary_zh: 面向产品、供应商、认证实验室、云服务与上下游团队的 PCR02 海外产品化协作说明，定义目标、当前阶段、交付物、责任边界和放行门禁；不包含内部实现、凭据、端点或安全细节。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: reviewed
---

# PCR02 海外产品化协作对齐说明

**文档用途**：用于产品、硬件、固件、App/云、质量、认证实验室、供应商和渠道伙伴之间对齐海外产品化范围、交付物与门禁。

**当前版本属性**：协作草案，基于 2026-09-03 的工程证据整理；不是认证报告、法律意见、报价依据、上市承诺或符合性声明。

## 1. 核心结论

PCR02 已具备联网、远程服务、软件升级、产测和设备验证的工程基础，但仍处于产品化和合规证据收敛阶段。当前不能以已有开发、测试框架或样机能力，声明产品已可在 EU、UK 或美国量产销售。

首发上市的判定必须同时满足：目标市场与 SKU 已冻结、适用认证完成、安全更新与设备安全能力可验证、隐私和云服务边界已确认、量产追溯与实机可靠性证据已闭环。

## 2. 对齐范围

首轮对齐默认覆盖 EU、UK 和美国的消费级联网机器人场景，包含：

- Wi-Fi 联网、云服务、App、音视频或遥测能力；
- 含电池、充电、驱动机构、传感器与软件升级能力的整机；
- 产品设计、供应链、认证、制造、软件安全、隐私、售后与召回准备。

实际适用法规、标准、测试量和责任主体，以最终销售国、产品类别、无线模组、天线、充电器、电池、外壳、云部署区域和销售渠道为准。

## 3. 当前阶段与共识

| 领域 | 当前阶段 | 面向外部伙伴的协作结论 |
| --- | --- | --- |
| 产品定义 | 待冻结 | 请先确认首发国家、SKU、核心功能、销售渠道与目标用户 |
| 硬件认证 | 待启动/待取证 | 需冻结样机配置后确认测试计划、实验室与整改节奏 |
| 固件安全 | 方案完善中 | 安全更新、设备身份、防回滚和恢复能力需形成可验证产品方案 |
| 云与隐私 | 边界待确认 | 需确认数据流、区域、第三方服务、留存、删除和用户告知 |
| 量产质量 | 工程资产已具备部分基础 | 需转化为批次放行、校准、追溯和实机可靠性证据 |
| 上市/售后 | 待规划 | 需准备标签、说明书、支持期、漏洞响应、客服和召回机制 |

## 4. 各方需要交付的内容

| 协作方 | 需对齐或交付 | 最小输出 |
| --- | --- | --- |
| 产品/市场 | 首发市场、SKU、定位、渠道、用户和上市节奏 | 市场与 SKU 冻结表、需求优先级 |
| 硬件/供应商 | BOM、无线模组、天线、电池、充电器、外壳和变更控制 | 最终 BOM、规格书、变更清单、样机一致性声明 |
| 认证实验室/合规 | 法规适用性、测试计划、样机数量、整改与报告 | 认证矩阵、报价/周期、测试报告、DoC 支持材料 |
| 固件/安全 | 可信升级、设备身份、密钥、漏洞响应和安全支持期 | 安全架构、威胁模型、验证计划、支持期说明 |
| App/云/第三方服务 | 区域可用性、数据流、账户/绑定、隐私、服务连续性 | 数据流图、数据处理边界、区域部署和 SLA |
| 质量/制造 | 校准、老化、功能放行、版本追溯、异常处置 | 产测规范、校准/老化记录、批次追溯格式 |
| 售后/渠道 | 本地语言资料、保修、升级支持、漏洞入口和召回 | 用户资料、服务政策、支持与事件响应流程 |

## 5. 产品化门禁

### Gate A：市场与配置冻结

- 明确首发国家/地区、销售主体、渠道和目标用户；
- 冻结整机 SKU、无线模组/天线、电池、充电器、外壳、地区软件和云服务区域；
- 建立变更控制：影响认证、安全或隐私的变更必须重新评估。

### Gate B：法规、硬件与安全设计确认

- 完成适用法规、认证、标签、环境和运输要求矩阵；
- 形成整机无线、EMC、安全、电池、充电和可靠性测试计划；
- 形成设备安全基线：唯一身份、无弱默认凭据、安全更新、漏洞报告入口和支持期；
- 形成隐私与数据治理设计：数据流、地区、留存、删除、第三方处理和用户告知。

### Gate C：工程验证与认证证据

- 最终样机与送检配置一致，完成适用测试和整改；
- 软件升级、异常恢复、联网、充电、运动、传感器和关键安全场景完成实机验证；
- 发布制品与版本、配置、SBOM、签名和适用硬件建立可追溯绑定；
- 完成生产校准、老化、批次放行和异常处置演练。

### Gate D：上市与运营准备

- 完成适用的认证文件、DoC、标签、说明书、警示语和线上销售信息；
- 完成隐私政策、服务条款、用户支持、最短安全支持期和漏洞披露入口；
- 完成售后、事故通报、召回和服务连续性流程。

**任一 Gate 未完成时，项目维持“开发/验证中”，不升级为“可上市”。**

## 6. 优先级建议

### P0：上市前必须闭环

- 首发市场与 SKU 冻结；
- 认证矩阵、测试计划和一致样机；
- 可信升级、设备安全和恢复机制；
- 无线、整机安全、电池/充电与关键风险场景实机验证；
- 数据与隐私边界、用户告知、删除/解绑能力；
- 量产追溯、批次放行和支持/漏洞响应机制。

### P1：首发商业化前完成

- SBOM、许可证和第三方供应链治理；
- 长周期可靠性、弱网、运输与环境适应性验证；
- 本地化资料、客服、保修、回收与渠道资料；
- 灰度升级、监控和服务运营能力。

### P2：规模化阶段持续建设

- 多区域数据治理与服务容灾；
- 漏洞、召回与事故响应演练；
- 质量趋势、现场失效率和供应链持续审计。

## 7. 会议建议与待决事项

首次跨团队会议建议先确认以下事项，避免在不确定 SKU 上开展无效认证或返工：

1. 首发市场顺序：EU、UK、美国是否同时推进；
2. 最终产品配置：无线方案、天线、电池、充电器、传感器、音视频和云服务；
3. 面向家庭、宠物或儿童场景的产品边界与安全警示；
4. 云服务和第三方服务的地区、数据处理角色与商业可用性；
5. 安全更新支持年限、漏洞响应责任和售后主体；
6. 认证样机、量产样机和最终软件版本的变更控制机制；
7. 各项交付物 owner、计划日期、依赖项和验收人。

## 8. 信息边界与使用方式

本文件可用于协作和范围对齐，但外发前仍应由产品/法务/合规负责人确认版本和收件人范围。本文不包含实现细节、内部代码路径、原始日志、设备/服务端点、凭据、密钥、漏洞复现细节或未公开的供应商信息。

内部工程证据、风险推导和详细缺口保留在关联的内部归档中，由授权人员按需查阅。外部伙伴只需依据本文件提供其负责领域的规格、报告、计划和验收证据。

## 9. 归档治理

- Source：内部产品出海就绪度评估的脱敏协作派生版本。
- Topic：`pcr02-overseas-product-alignment-brief`。
- Sanitization：删除内部源码路径、实现弱点、端点、凭据、原始日志和未公开供应链信息。
- Verification：本文内容已进行脱敏与结构检查；法规适用性、认证结论和外发许可仍需相关 owner 复核。
- Memory Candidate：否。
- Gate Result：`reviewing`；等待市场/SKU、合规和外部协作方确认。
