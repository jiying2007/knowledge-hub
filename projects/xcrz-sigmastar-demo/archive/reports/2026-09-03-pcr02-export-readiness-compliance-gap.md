---
id: pcr02-export-readiness-compliance-gap-20260903
title: PCR02 产品出海就绪度与合规缺口归档
kind: project-archive
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/reports/2026-09-03-pcr02-export-readiness-compliance-gap.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
related:
- projects/xcrz-sigmastar-demo/validation/2026-07-31-app-sensor-test-comprehensive-closure.md
- projects/xcrz-sigmastar-demo/current/designs/2026-08-03-pcr02-sensor-wifi-multi-network-design.md
source:
  type: current-codex-session-source-inspection-and-regulatory-research
  from: 2026-09-03 PCR02 源码、独立应用文档、项目知识库与官方 EU/UK/US 监管页面的只读评估
  temporary_source_retained: false
review_after: '2026-12-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize launch, certification, legal conclusion, or owner acceptance
tags:
- pcr02
- export-readiness
- product-readiness
- compliance
- ota
- cybersecurity
- privacy
- wireless
- battery
- hil
validation_refs:
- projects/xcrz-sigmastar-demo/archive/reports/2026-09-03-pcr02-export-readiness-compliance-gap.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: source-inspection-and-regulatory-research-hil-pending
evidence_refs:
- app_ota/app_ota.c
- app_ota/docs/TECHNICAL_DESIGN.md
- app_ota/docs/DEVELOPMENT_PLAN.md
- app_sensor_test/COMPLETION_AUDIT.md
- app_product_test/docs/DEVELOPMENT_PLAN.md
- 多WiFi存储与切换实现方案.md
- https://single-market-economy.ec.europa.eu/sectors/electrical-and-electronic-engineering-industries-eei/radio-equipment-directive-red_en
- https://www.gov.uk/guidance/regulations-consumer-connectable-product-security
- https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/online-tracking/guidance-for-consumer-internet-of-things-products-and-services/
- https://docs.fcc.gov/public/attachments/FCC-26-51A1.pdf
created_at: '2026-09-03'
updated_at: '2026-09-03'
captured_at: '2026-09-03'
last_verified: '2026-09-03'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-03'
manual_validation_pending: true
summary_zh: PCR02 已具备部分联网、OTA、产测与测试框架能力，但可信升级、认证、隐私、SBOM、量产追溯与目标板 HIL 未闭环，不能标记为 EU、UK 或美国市场产品就绪。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: reviewed
---

# PCR02 产品出海就绪度与合规缺口归档

## 1. 结论边界

本文将 PCR02 作为带 Wi-Fi、云连接、音视频/遥测、锂电池、充电、电机和 OTA 能力的消费级联网机器人，整理 EU、UK 和美国首发需要的工程与合规准备度。

截至 2026-09-03，结论为：**PCR02 只能判为 source/功能资产部分具备、产品就绪度 blocked；不得声明可在 EU、UK 或美国量产销售。**

本文不是法律意见、认证报告、符合性声明（DoC）或 owner 签收。最终法规、标准和试验计划必须在首发市场、SKU、无线模组/天线、电池、充电器和云服务地域冻结后，由合规负责人和认可实验室确认。

本文不保存设备或服务端点、真实用户/设备标识、SSID、密码、token、cookie、原始日志、二进制或密钥材料。

## 2. 证据分层

| 层级 | 应有证据 | 当前状态 |
| --- | --- | --- |
| Source/SIL | 源码、设计、Host/静态/构建 | 仅能确认部分功能和文档意图；本次未重跑构建 |
| 产品依赖 | 最终硬件、模组、天线、电池、充电器、第三方组件、地区配置 | 首发 SKU 未冻结 |
| 制品身份 | revision、签名、SBOM、配置、校准与待售镜像的绑定 | 未见正式发布制品链 |
| Board/HIL | 真实硬件、仪器、异常路径、恢复、长循环 | 框架存在，完整实机证据缺失 |
| 外部签收 | 实验室报告、DoC、供应商材料、市场责任人签收 | 未见相应材料 |

Host、静态分析或交叉编译通过，不能替代认证、整机安全、目标板 HIL 或法律责任证据。

## 3. 市场门槛

### EU

- 带无线功能的终端通常按 RED 评估无线、EMC、健康安全、频谱和适用网络安全要求；Delegated Regulation (EU) 2022/30 已自 2025-08 适用，后续与 CRA 的衔接需按最终产品确认。
- 还需逐项核对 RoHS、REACH、WEEE、包装、外部电源、一般产品安全和当地语言资料。
- 含锂电池时，还需按 Battery Regulation (EU) 2023/1542、运输和产品类别核对信息、回收、可更换性和供应链义务。
- 线上销售还需制造商/欧盟责任人、产品识别、警示和事故/召回流程。

### UK

- 无线、EMC、安全和 UKCA 的适用范围须按最终 SKU 和供应链确定。
- PSTI 对消费者联网产品要求：禁止通用/易猜默认密码、提供漏洞报告渠道、公布最低安全更新期，并提供 Statement of Compliance。
- 对家庭 IoT 的个人信息处理，应按 UK GDPR、PECR 和 ICO 指引完成默认隐私保护及必要的 DPIA。

### 美国

- 带 Wi-Fi 发射能力的终端通常须按 FCC Part 15 的设备授权路径确认；结果必须覆盖实际模组、天线、功率、外壳和区域固件。
- UL/NRTL、适配器、电池、运输、环保和零售渠道义务需按州、产品类别与渠道另行确认，不能由 FCC 或源码结果替代。

## 4. 当前能力与缺口矩阵

| 域 | 可见能力 | 不满足或无证据 | 结论 |
| --- | --- | --- | --- |
| 无线/EMC | 有 Wi-Fi 配网和网络组件 | 未见最终 RF BOM、天线矩阵、预扫、FCC/RED/UKCA 报告或 DoC | blocked |
| 电池/充电/运动安全 | 有电池、电机、上桩、温度和产测设计 | 未见运输/安全报告、温升、异常充电、误运动、跌落或 ESD 证据 | blocked |
| OTA | 包预检、路径限制、MD5、锁、状态、升级顺序和恢复设计 | 缺少密码学签名、可信根、防回滚、安全启动和板端闭环 | needs-fix |
| Wi-Fi 凭据 | 目标方案定义最小化传递、统一入口和事务需求 | 当前方案记录多项凭据生命周期、日志、持久化、命令覆盖与内存安全问题 | needs-fix |
| 设备安全 | 可见 HTTPS/证书资源、解绑和诊断路径 | 未见唯一设备身份、密钥注入/轮换、漏洞披露、支持期和 CVE 流程 | blocked |
| 隐私与云 | 有绑定、遥测和联网服务路径 | 未见数据流、保留、DPIA、跨境、删除权、第三方处理协议和告知证据 | blocked |
| 开源供应链 | 使用大量第三方组件与预编译库 | 未见产品级 SBOM、许可证义务清单、SCA/CVE 和制品绑定 | blocked |
| 量产/HIL | 有产品测试和 Sensor 测试框架 | 多项板端/恢复验证待完成；未绑定量产制品、校准和长循环证据 | blocked |

## 5. 关键技术事实

### 5.1 OTA 当前仅保证完整性，不能证明更新来源可信

`app_ota` 对 `guide.toml` 内的组件 MD5 做比对，并保存一个重复包标识。该标识由包的大小、修改时间和路径构成，目的是避免重复处理，并非密码学签名。

主要阻断项：

1. MD5 和声明 MD5 的 `guide.toml` 同在升级包内，不能抵抗恶意包内容和元数据的同步替换。
2. 当前没有证据证明存在私钥签名、公钥验签、设备侧信任根、密钥轮换或镜像验签链。
3. 默认版本策略是不同版本即可升级；`higher` 为可选 CLI 参数，未形成不可篡改的安全版本计数器。
4. 代码检索未找到可复核的 secure boot、反回滚计数器或恢复分区设计；这应表述为“无证据、需专项核对”，不等于断言平台绝对没有该能力。
5. OTA 计划仍将 SDK 构建、脚本检查、无效包、单组件、SoC、失败恢复和主业务恢复列为待验证。

整改目标：受控离线私钥签名 manifest；设备侧信任根验签；绑定型号、硬件版本、组件 hash 与最低安全版本；强制反回滚和可恢复分区；最终镜像、签名、SBOM、revision 与板端结果一一绑定。

### 5.2 Wi-Fi、凭据和隐私风险已被目标设计明确记录

多 Wi-Fi 文档明确为目标方案，不是当前能力声明。其“当前缺口”列出：部分命令不支持、明文密码长期驻留、持久化事务不完整、失败可能丢失旧配置、敏感凭据日志、密码长度/隐藏网络不足、第二写入口、缓冲区风险，以及 Task/Iot 缺少匹配源码与发布链。

整改原则：凭据只在必要操作窗口存在；查询、状态、日志和证据包不返回密码；统一写入口；原子 prepare/commit/abort 和回滚；唯一可验证持久化路径与权限；解绑/恢复出厂覆盖端、App、云和第三方身份与数据清理。

### 5.3 测试框架不能替代实机产品证明

`app_sensor_test` completion audit 将完整目标标为 `needs-external-evidence`，明确 Source/Host/ARM 结果不能替代 Board JSONL、仪器、制品身份、恢复状态与 HIL bundle。运动、光学、声学、电源、OTA 和 soak 仍需真实设备与 owner 证据。

`app_product_test` 开发计划仍有充电温度、存储故障、断电恢复、组件故障注入、老化终态等板端待验证项。出海放行必须绑定冻结的硬件、固件、校准和量产测试记录。

## 6. 放行门禁与优先级

### P0：未完成不得开始海外量产销售

1. 冻结首发国家/地区、SKU、无线模组/天线、电池、充电器、外壳、云区域和 App 版本。
2. 完成法规/认证矩阵，并取得适用的实验室报告、DoC、标签和责任主体证据。
3. 完成可信 OTA、安全启动链、设备身份/密钥注入、密钥轮换、反回滚与恢复验证。
4. 修复 Wi-Fi 凭据、日志脱敏、解绑/擦除和已知高风险持久化/事务问题。
5. 完成上桩、脱桩、堵转、异常充电、掉电、升级失败、网络故障、传感器失效和恢复的安全 HIL。
6. UK 准备 PSTI Statement of Compliance、漏洞披露入口和最低安全更新支持期。

### P1：首发前完成

1. SPDX/CycloneDX SBOM、许可证义务、SCA/CVE 基线和修复 SLA。
2. 数据流、隐私政策、DPIA/等价评估、留存/删除、跨境与第三方处理协议。
3. 量产校准、老化、序列号/密钥/版本绑定和出厂证据留存。
4. 温升、跌落、振动、ESD、弱网、长循环和目标地区 Wi-Fi 兼容性测试。
5. 当地语言的说明书、警示、保修、回收与售后支持资料。

### P2：规模化运营前完成

1. 灰度发布、隐私脱敏遥测、崩溃/安全事件和事故通报流程。
2. 漏洞、召回、密钥泄露和云服务故障恢复演练。
3. 多区域数据治理、供应链持续审计和现场失效率趋势闭环。

## 7. 责任交付物

| 交付物 | 建议责任方 | 最小验收证据 |
| --- | --- | --- |
| 市场/SKU 合规矩阵 | 产品、法务、合规 | 法规、标准、SKU、实验室、责任人、截止日期 |
| 认证技术文件 | 硬件、射频、实验室 | RF/EMC/安全/电池报告、BOM、标签、DoC |
| 可信启动与 OTA | SoC、MCU、固件、安全 | 威胁模型、密钥生命周期、签名、防回滚、恢复 HIL |
| 设备安全基线 | 安全、固件、云 | 唯一身份、无弱默认口令、漏洞入口、支持期、CVE 流程 |
| 隐私治理包 | 产品、法务、云、App | 数据流、DPIA、告知、留存/删除、跨境与 DPA |
| SBOM/供应链包 | 发布、供应链、安全 | SBOM、notice、SCA/CVE、制品 hash |
| 量产放行包 | 制造、质量、固件 | 校准、老化、追溯、抽检和异常处置 |
| HIL/可靠性包 | 验证、硬件、固件 | 制品身份、仪器/阈值、短循环、soak、恢复结论 |

## 8. 验证、外部来源与治理

本次完成的是源码/文档只读评估、项目知识上下文核对和官方监管资料研究。未执行设备操作、构建、签名验证、实验室测试、认证申请或法律审查。因此本文保持 `reviewing`，所有 P0/P1 项均需独立验证和 owner 接受。

外部来源仅记录事实性摘要和 URL，不复制长文本；法规具有时效性，使用前必须复核：

- European Commission, Radio Equipment Directive (RED), retrieved 2026-09-03.
- UK Government, Regulations: consumer connectable product security, retrieved 2026-09-03.
- UK ICO, Guidance for consumer Internet of Things products and services, retrieved 2026-09-03.
- US FCC, equipment authorization / Part 15 material, retrieved 2026-09-03.
- European Commission, Batteries Regulation overview, retrieved 2026-09-03.
- EUR-Lex, Regulation (EU) 2023/988 (GPSR), retrieved 2026-09-03.

- Source：当前 Codex 会话、项目源码/文档、项目知识库和公开监管页面。
- Topic：`pcr02-export-readiness-compliance-gap`。
- Archive Candidate Path：本文 front matter 的 `path`。
- Sanitization：未写入端点、用户/设备标识、凭据、原始日志、二进制或密钥。
- Verification：仅 source inspection 与研究完成；认证、法律、最终制品、HIL 和 owner acceptance 缺失。
- Memory Candidate：否；本文不自动更新 memory 或 AGENTS。
- Gate Result：`blocked`；缺少 P0 外部和板端证据。

## 9. 补充论证：硬件、固件、软件、量产逐项判断

本节补齐首次评估的完整论证。它与前文的短矩阵共同构成归档的判断依据；若二者发生冲突，以本节的“证据边界”和 `blocked` 结论为准。

### 9.1 硬件与认证

#### 无线与电磁兼容

PCR02 具备 Wi-Fi、云连接、视频和音频等联网特征。首发 EU/UK/美国前，必须冻结 Wi-Fi 模组、天线、外壳、线束、充电器和整机 SKU，再对固定配置送检。EU 无线产品需按 RED 确认；美国带 Wi-Fi 发射功能通常属于 FCC Part 15 intentional radiator；UK 还需纳入联网消费品的 PSTI 网络安全义务。

截至本次检查，未发现可交付的 FCC、CE/RED、UKCA 测试报告、DoC、天线/BOM 冻结记录、射频区域配置矩阵或实验室整改闭环。因此“板子能联网”不能替代无线合规。

#### 电池、充电、运输与环保

含锂电池、充电座或适配器时，上市门槛至少包括：

- 电芯/电池包一致性、保护板、短路、过充、过放和热失控风险评估；
- UN 38.3、空运/海运资料、包装和标签；
- 目标市场的电池安全、充电器安规、整机异常充电与温升测试；
- EU 电池、回收、信息、可持续和追溯义务；
- RoHS、REACH、WEEE、包装环保和本地语言标签。

仓内能看到充电、电机、温度和老化相关设计，但这不是认证证据。`app_product_test` 仍列有充电温度、掉电恢复、存储异常和传感器故障注入等板端待验证项。因此电池/充电安全只能判为“工程验证未完成”，不能判为可出海。

#### 机器人本体安全与可靠性

移动、带电机、红外/激光、摄像头和音频的消费机器人，应覆盖防夹、防误运动、失控后的安全状态、上/脱桩、接触不良、堵转、轮子悬空、传感器失效、温升、跌落、运输振动、ESD/EFT、湿热、高低温、老化，以及宠物/儿童误用和警示语。

`app_sensor_test` 的完成性审计明确将完整能力标为 `needs-external-evidence`。其 dock-cycle 方案是“人工监管 + fail-fast”，不能包装成已证明的物理停机安全；运动、光学、声学、电源、OTA 和 soak 的 Board/HIL 仍需最终制品身份和外部裁决。

### 9.2 固件安全

#### 可信 OTA 的目标架构

当前 OTA 应定位为工程升级工具，不能定位为海外消费产品的安全更新机制。目标链应为：

```text
离线 HSM 或受控私钥签名
        ↓
签名 manifest：型号、硬件版本、组件版本、hash、最低安全版本
        ↓
设备内置或安全区保存的公钥 / 可轮换信任根
        ↓
bootloader 验签 → OS/rootfs 验签 → App/MCU/电机镜像验签
        ↓
不可回退安全版本计数器 + A/B 或等价可恢复分区
```

除签名外，必须验证掉电、升级中断、网络异常、单组件升级失败、主业务恢复、版本拒绝、密钥轮换和回滚恢复。最终板端测试必须绑定正式镜像的 revision、hash、签名和硬件配置。

#### 设备身份、密钥与漏洞治理

联网产品至少需要每台设备唯一且不可预测的身份和密钥；禁止通用/弱默认密码；安全配网、鉴权、证书生命周期、吊销/轮换；持续的 CVE/SBOM 扫描与修复流程；公开漏洞披露渠道与 SLA；用户可见的最短安全更新支持期与 EOL 政策。

目前未发现产品级 SPDX/CycloneDX SBOM、第三方许可证义务审查、持续 CVE 修复承诺、漏洞披露政策、安全更新期限，或设备唯一密钥/证书注入与轮换设计证据。仓内存在大量第三方组件和预编译库，因此此项不能后置为临发布整理工作。

### 9.3 软件、云与隐私

HTTPS、证书文件、设备绑定/解绑、遥测和音视频能力只是起点，并不等于隐私合规。对于 EU/UK 家庭 IoT，涉及摄像头、麦克风、设备标识、家庭 Wi-Fi、行为遥测和云端绑定时，至少应具备：

- 端、App、云和第三方音视频/AI 服务的数据流与留存表；
- 控制者/处理者角色、跨境传输和第三方数据处理协议；
- 首次启用告知、摄像/录音指示、同意/撤回与儿童/家庭场景保护；
- 默认最小化采集、默认最短留存和非必要采集默认关闭；
- 导出、删除、解绑、恢复出厂后的端云双侧删除验证；
- DPIA 或等价的数据保护风险评估与版本追溯。

当前未看到上述闭环证据，应表述为“治理和验证缺失”，而不是断言代码必然违法。

### 9.4 量产、上市与售后

首发 SKU 的发布门禁应至少包括：

1. 冻结硬件 BOM、无线模组/天线/充电器、地区 SKU 和软件版本；
2. 建立 EU、UK、US 的法规、标准、实验室、样机、报告、标签和责任人矩阵；
3. 建立主板、模组、电池、固件、密钥注入、校准、老化和最终测试结果的制造追溯；
4. 将产测升级为批次放行证据，覆盖校准、异常注入、存储断电、充电温度、传感器、Wi-Fi、音视频和恢复出厂；
5. 建立不可变发布身份：Git revision、编译环境、SBOM、镜像 hash、签名、适用硬件版本和回滚策略；
6. 建立安全支持年限、漏洞入口、版本兼容表、事故通报、远程禁用/召回和客户支持流程。

EU 在线销售还应显示制造商或欧盟责任人、产品识别和适用语言的警示/安全信息；产品安全事故需要按适用机制通报。

## 10. 归档后的执行顺序

1. 产品负责人冻结首发市场和 SKU，形成合规矩阵的唯一输入。
2. 硬件/合规负责人确定实验室与样机配置，禁止在认证过程中变更天线、模组、外壳、电池、充电器或区域固件而不重新评估。
3. 安全/固件负责人先完成可信启动、可信 OTA、设备身份和凭据/日志整改设计，再进入板端验证。
4. 云/App/法务负责人完成数据流、DPIA、隐私告知、跨境与第三方处理边界。
5. 验证/质量负责人以冻结制品开展 P0 HIL、可靠性和量产放行测试；Host/SIL 结果仅作为前置证据。

上述顺序中任何一项缺失，都不应将 PCR02 的状态从 `blocked` 提升为产品就绪。
