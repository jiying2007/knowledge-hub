---
related:
- projects/mcu/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_status: null
decision_date: null
id: mcu-second-product-engineering-foundation-plan-20260924
title: 第二产品 MCU 研发基础设施建设计划
kind: decision
domain: projects/mcu
path: projects/mcu/decisions/second-product-engineering-foundation-plan.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: 本次用户需求和工作区只读审查，尚无已登记 source id
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-10-24'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- mcu
- second-product
- engineering-foundation
validation_refs:
- projects/mcu/decisions/second-product-engineering-foundation-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/mcu/decisions/second-product-engineering-foundation-plan.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-24'
updated_at: '2026-09-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-24'
manual_validation_pending: true
summary_zh: 第二产品选型前建立代码规范、组件边界、项目模板、测试与制品身份，量产产品保持维护边界。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- 第二产品 MCU 研发基础设施建设计划
---

# 第二产品 MCU 研发基础设施建设计划

> 状态：`reviewing`。本文是 2026-09-24 根据用户提出的“量产产品不重构、第二产品按规范实施”及 MCU 工作区只读审查形成的执行计划候选。任务、工时和门禁待研发、硬件、测试及发布责任人评审；本文不代表 owner 批准或产品发布就绪。

## 摘要与目标

在第二产品芯片、板卡和源码归属尚未确定时，先建设团队可复用的研发入口：代码与接口规范、组件准入规则、项目模板、协议测试向量、质量门禁和产品身份契约。选型后据此开发主板、电机与充电桩 MCU，并用目标板验证。第一产品继续按既有量产流程维护，不承担目录迁移、统一框架改造或批量接口重写。

| 目标 | 可验收的结果 |
| --- | --- |
| O1 可复现启动 | 非模板作者从全新克隆完成工具链核验、示例构建、主机测试和包检查；流程不依赖个人路径或缓存。 |
| O2 边界明确 | 产品策略、板级适配、芯片驱动、协议/算法组件的依赖方向有图和接口；至少两个样例组件可独立编译、测试。 |
| O3 规范可执行 | 统一入口运行格式、告警、静态检查、行为测试、交叉构建和包校验；故意引入的违规用例能触发失败。 |
| O4 跨板兼容 | 发送端和接收端消费同一协议向量；不兼容的版本、字段、超时或升级顺序变化需要共同评审。 |
| O5 制品可追溯 | manifest 绑定产品、板卡角色与硬件版本、固件与协议版本、源码提交或第三方输入哈希、工具链及验证层级；错板包在烧录前被拒绝。 |

## 适用范围与约束

- **适用**：MCU 产品组的第二产品立项与开发准备，以及以后新建项目的团队工程资产。
- **量产边界**：GD32L235、HC32F072、MM32SPIN023C 的现有量产仓仅作为行为和发布经验来源；必要安全、缺陷和生产维护继续按原仓受控实施。本文不要求其迁移到新模板。
- **待选型**：具体 MCU、引脚、电池 profile、Flash 布局、升级链路、工装参数和 HIL 数值不在选型前冻结；每项在硬件资料与责任人确认后进入板级配置。
- **资产归属**：跨项目决策与复用经验留在 Knowledge Hub；项目模板、检查脚本、schema 和样例组件放在对应受管源码仓。一个契约只有一个可编辑正文，其余位置引用。
- **复用准入**：现有产品代码可作为行为参考；只有接口稳定、主机测试可跑、消费方验证可跑且许可与资源预算明确时，才提升为共享组件。

## 源事实与问题依据

截至 2026-09-24，本地只读审查确认：`workspace://gd32l235/App/README.md` 所述六层目录与实际目录不一致；`workspace://gd32l235/App/CMakeLists.txt` 和 `workspace://hc32f072/App/CMakeLists.txt` 主要把应用汇成单目标；GD32 `protocol.c` 包含三个 handler 的 `.c` 文件，`bsp.h` 暴露跨模块可写状态；电池 profile 和充电参数位于现有产品源码中。发布 profile 以芯片命名，现行 manifest 缺少强制产品和板级兼容身份。上述观察说明新产品需要先建立契约，**不等于**已证明量产固件存在运行时故障。

发布工具的 25 项单测、工具链结构检查、GD32/HC32 快速检查在本会话通过；快速检查复用已有构建报告。GD32 的 `codex` gitlink 缺少 `.gitmodules` 映射，递归子模块检查报错。上述结果均不替代新鲜交叉构建、烧录回读、跨板联调或 HIL。

## 任务包与完成定义

每项指定一位交付 owner；表中角色是建议分工，尚未视为人员签收。估时为单项粗估人日，不含板卡等待和团队评审排期。共享 schema、根配置与发布契约串行写入。

| ID | 建设任务与建议 owner | 交付物 | 独立验收 | 依赖 / 估时 |
| --- | --- | --- | --- | --- |
| T01 | 冻结量产维护和新产品范围；研发负责人 | 范围表、变更路径、资产 owner 表 | 每项资产有唯一维护者；量产修复与新产品开发的审批和验证路径可区分 | 无 / 1–2 |
| T02 | 制定 C 代码与评审规范；固件架构 owner | 命名、单位、头文件最小依赖、公开 API、错误语义、超时、ISR/前台共享状态、日志和第三方代码边界 | 选 GD/HC 各一文件试评审；每条强制项有机器检查或明确人工检查点 | T01 / 2–3 |
| T03 | 冻结模块依赖及组件准入；架构与板卡 owner | 依赖方向图、组件接口模板、产品配置注入规则、例外登记 | 可判断协议解析、充电判定、电池 profile、GPIO 分别归属何处；设计中无跨板芯片头依赖 | T01 / 2–3 |
| T04 | 建立最小新项目模板；构建 owner | 源码布局、CMake 目标、工具链清单、统一命令、README、示例包 | 非作者在全新克隆和非仓库 cwd 完成 help、构建、主机测试、包检查 | T02–T03 / 3–5 |
| T05 | 建立两个纵向组件样例；组件 owner | 建议采用协议帧解析及无硬件依赖的状态判定；含 API、实现、主机测试、使用说明 | 各自独立编译；正常、边界和非法输入测试通过；替换板级输入不改组件实现 | T03–T04 / 各 2–4 |
| T06 | 固化跨 MCU/SoC 协议契约；各链路 owner | 字段、单位、字节序、版本、超时、错误和升级序列；可执行向量 | 同一向量在发送编码与接收解码两侧运行；不兼容修改需要消费者共同评审 | T03 / 3–5 |
| T07 | 接入质量门禁；测试与构建 owner | format、告警、静态检查、主机行为测试、交叉构建、包检查的统一入口和 CI | 分别注入格式错误、越层依赖、测试失败、镜像超预算，门禁确实失败；正常样例通过 | T04–T05 / 3–5 |
| T08 | 定义产品与制品身份；发布 owner | 产品、板卡角色、硬件修订、固件/协议兼容 schema，manifest 与烧录前校验 | 错产品、错硬件修订、错镜像角色均被拒绝；正确包保留来源哈希、工具链和验证层级 | T01、T04 / 3–5 |
| T09 | 建立 HIL/产线证据模板；测试与硬件 owner | 板级矩阵、波形/日志索引、烧录回读和故障复现记录 | 缺板卡版本、包哈希或实测结果不能标通过；三类 MCU 及 SoC 均可按模板记录 | T06、T08 / 2–3 |
| T10 | 独立试用和修订；第二产品工程师 | 两人从零启动记录、阻塞清单、修订版模板 | 两位非模板作者独立定位命令并完成样例闭环；阻塞项关闭或登记责任人与期限 | T04–T09 / 2–3 |

T02/T03 应先统一术语和接口边界；T04 之后才开始 T05/T07。T06 与 T08 可以由不同 owner 推进，但跨板协议字段与 manifest schema 各由单一 owner 写入。关键路径为 `T01 → T03 → T04 → T05 → T07 → T10`。估时在 owner 接收、第二产品需求包出现后重新评估。

## 阶段门槛与证据

| 门槛 | 触发时点 | 必需证据 | 不通过时的处理 |
| --- | --- | --- | --- |
| M0 团队资产可用 | 芯片选型前 | T01–T10 中不依赖器件的交付物；全新克隆演示；独立组件测试；错误注入门禁；示例包身份校验 | 保持 `reviewing`，不以文档完成代替可运行模板 |
| M1 产品与板级契约冻结 | 芯片、封装和硬件资料确定后 | 每板芯片/封装、Flash/RAM、引脚、电源与复位、调试烧录、配置参数、接口及升级路径的资料来源和 owner 复核 | 未确认项目不得生成“量产兼容”配置 |
| M2 板级 bring-up | 样板可测试后 | 三类 MCU 的 fresh cross build、烧录回读、基本外设和故障路径；跨板协议、断电恢复、升级/回退；均绑定板号和包哈希 | Host、构建、设备证据分别报告，缺项保留未验证 |
| M3 集成与发布准入 | 产品集成与发布前 | 兼容矩阵、消费者评审、容量余量、HIL、产线流程、manifest、回退和责任人签收 | 缺任一强制证据不得声称产品发布就绪 |

最先执行 T01–T04 与 T08 的 schema 草案。第一轮样例评审后再推进 T05–T07，以实际编译和错误注入校验规范是否可执行。M0 通过后，第二产品新仓从模板创建；M1 前不预制芯片 BSP。

## 建议的团队工作方式

- 研发负责人维护范围和优先级；架构 owner 维护接口与组件准入；板卡 owner 维护具体 BSP 和产品参数；测试 owner 维护行为与 HIL 证据；发布 owner 维护 manifest、签名/哈希、烧录和回退入口。
- 每个公开接口、协议字段、产品兼容 schema 和发布门禁由一个写入 owner 负责，消费者参与评审；不能以“多人共同负责”替代落地责任。
- 新成员培训以 T10 的独立试用为验收，不以阅读文档或参加会议作为完成证明。
- 资产复用评审记录适用范围、资源成本、消费者数量、测试证据、版本和回退方式；未达准入条件保持项目内实现。

## 待 owner 决策的问题

1. 确认 T01–T10 的实际负责人、优先级、人力预算和首个样例组件。
2. 确认第二产品是否要求与第一产品线协议或 OTA 兼容；未确认前不得默认兼容。
3. 确认 M0/M1/M2/M3 各门槛的签收角色，以及 HIL 哪些项目为阻断项。
4. 决定 GD32 `codex` gitlink 元数据缺口的独立维护排期；它是可复现性问题，不纳入第二产品源码重构。

## 风险、验证与 Review

- **风险**：选型未定会使 BSP 和测试数值过早固化；单纯复制 PCR02 会引入电池、时序和协议隐含假设；仅凭静态源码检查会高估组件与产品就绪度。
- **回退**：候选规范或模板未通过 M0 时保持 reviewing；第二产品仍可按已签收的最小契约开发，失败组件不提升为团队共享资产。量产产品不依赖本计划的实施结果。
- **本文件验证**：检查 frontmatter/registry 一致性、Hub 链接与检索；任务实施验收须由各 owner 在相应源码仓、构建环境和实物板上另外执行。
- **Review owner**：`leiwenjun` 为 Hub 条目维护字段，本文无人工签收记录；实际任务 owner 仍待确认。`review_after=2026-10-24`，复核第二产品选型、M0 实施结果及任务估时。
