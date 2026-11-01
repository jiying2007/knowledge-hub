---
id: provider-c822be624c8ab61483a0ddc6fcfceccc1f615616262aa7fdf514c0db819c8db4
title: WIFI Camera Display保持SDK原生链路的源码收敛与验证
kind: validation
domain: projects/a123x
path: projects/a123x/validation/provider-c822be624c8ab61483a0ddc6fcfceccc1f615616262aa7fdf514c0db819c8db4.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:c822be624c8ab61483a0ddc6fcfceccc1f615616262aa7fdf514c0db819c8db4
  source_sha256: 43886cd489173834b9d7047152a3270bb58911ae94f61ef031f5f160f80470d1
  temporary_source_retained: false
review_after: '2027-01-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/a123x/validation/provider-c822be624c8ab61483a0ddc6fcfceccc1f615616262aa7fdf514c0db819c8db4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/validation/provider-c822be624c8ab61483a0ddc6fcfceccc1f615616262aa7fdf514c0db819c8db4.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-22'
updated_at: '2026-10-22'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-22'
manual_validation_pending: true
summary_zh: 2026-10-22。目标来自用户明确要求：尽量保持SDK基线和原生运行方式，覆盖Wi-Fi、Camera、Display及后续外围。本轮沿用前序先交付源码/测试的边界，不刷机、不提交推送，不声明完整固件或设备可用。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref: &id001
  type: project
  id: a123x
created_subject_ref: *id001
principal_id: local-user
provider_operation_id: c822be624c8ab61483a0ddc6fcfceccc1f615616262aa7fdf514c0db819c8db4
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- WIFI Camera Display保持SDK原生链路的源码收敛与验证
related:
- projects/a123x/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# Wi-Fi、Camera、Display向SDK原生链路收敛

2026-10-22。目标来自用户明确要求：尽量保持SDK基线和原生运行方式，覆盖Wi-Fi、Camera、Display及后续外围。本轮沿用前序先交付源码/测试的边界，不刷机、不提交推送，不声明完整固件或设备可用。

## 适配结论与落地

- 共同原则已写入release-tool/projects/SDK-INTEGRATION.md：原生目录/Makefile/Kconfig/安装/启动责任优先，板级差异进入DTS与配置，诊断不替换正常业务入口，不为新增用户态检查方便而改SDK默认策略。
- Wi-Fi：恢复meson64_f20_devwire_defconfig中的CONFIG_AMLOGIC_DTB_NODE_OPT=y；启动器移除/proc/device-tree强依赖，继续显式模式、cfg80211先加载、竞争owner拒绝、模块/四件套路径校验、有界insmod、重复启动不重载。DT标记/板型/模式一致性仍由静态包检查保证；DHD通过内核OF查找节点并校验GPIO。既有DHD代码/补丁未改变，新增真实补丁函数故障注入覆盖缺DT节点返回ENODEV且不申请GPIO，已有缺GPIO/冲突/IRQ失败清理检查保留。镜像门禁允许SDK节点优化，改核内核OF/SYSFS/cfg80211/外置DHD依赖，继续从实际boot/recovery提取并核对内嵌kernel.config身份。
- Camera：审计确认已沿sensor/Makefile、唯一libsns_sc5336p.so安装责任、ISP_SNS_OBJ_T与原生VI/MIPI/ISP/pipeline适配；保留正确接入，不新增另一采集框架。IO、有效IQ及CSI_CD/接收器/MCLK仍缺实板证据；实验IQ和ID/RAW诊断不默认升级为正式功能。
- Display：审计确认NV3006A在既有aml_spi_display目录作为库/显式诊断构建安装，未替换主屏或启动常驻显示服务；保留SDK主显示链路。Quad控制器/pinmap和线协议未验证，不以普通SPI或库构建成功冒充双屏支持。
- docs同步：产品README、项目WIFI-INTEGRATION、integration板级工具说明反映新方案。旧Provider候选provider-4a5583316170d16da4881d8e69e86c79b5cd56f1e07a22cc07b491ea0eaec891中“关闭节点优化”的方向已被本轮源码替换；旧记录仅保留历史，不作为当前实施建议。

## 新鲜验证

1. integration：rtk python3 -B -m unittest discover -s tests，210项，其中175项执行通过、35项按条件跳过，exit0。
2. project：rtk python3 -B -m unittest discover -s tools/codex_assets -p test_*.py，35项全部通过，exit0。
3. modules-port.sh --build --test：exit0；实际源码/补丁/固件来源校验、191条Sensor寄存器及114条屏初始化命令比对通过；7个AArch64制品架构检查通过；8组Host行为结果通过，含Wi-Fi无用户态DT目录、驱动加载失败和超时、Camera状态/IO/IQ/旧路径、Display故障隔离。硬件未操作，active_config_unchanged=true。
4. modules-port.sh --build --stage-root：exit0，隔离安装12个文件，Sensor库唯一、无实验IQ/RX默认安装、无Camera/Display新增自启动，仅产品Wi-Fi策略脚本；通用独立安装默认disabled。DEVWIRE defconfig的显式自动加载选项继续保留。
5. 六个相关源码仓git diff --check均exit0；drivers/of/base.c无修改。

隔离输出：.tmp/native-alignment-20261022/aarch64、host、staging。
f20-wifi-load SHA256=e0fdd4772976510067bcb4ebde7be1aad92003936ebbeced1365dcb0b03cf349；libsns_sc5336p.so构建输出=ed2bbd142945c1ce2487d216c906d137dd0f96cb5923f9f69f28ec662903287d；libnv3006a.so=77630f52f9e85a1f85c1e21a468f53bccc9c36dfa0bdbbe15f82580a942592d0。安装规则会strip Sensor库，因此安装hash与未strip构建输出不同。

## 负结果与边界

实施前另一个进程在共享SDK执行DEVWIRE完整构建，本轮配置/门禁修改与其冻结输入发生重叠。修改前锁检查不充分是本轮执行缺陷。该批.tmp/wifi-runtime-dt-build-20261022/build.json记录build_exit_code=0，但status=fail、exit_code=2，原因build rules changed during this operation; freeze edits and retry；它不支持本轮完整构建通过或有效包声明。未删除制品或终止该进程。随后通过现有workspace_lock获得本轮编辑互斥锁，完成剩余修改和隔离验证，并已正常释放（session67322 exit0）。不把该失败批次改成PASS、不使用其包交付。

当前生成的SDK内核.config仍可能对应失效批次中关闭优化的状态；只有DEVWIRE源码defconfig已恢复y。后续必须冻结最终源码，使用新的证据目录重新配置/构建/核包，再分别验证Wi-Fi枚举/固件/联网、Camera IQ/采集、Display实屏；源码、Host/AArch64、完整固件、设备HIL和owner批准独立。

## 收口

本轮software scope完成；全板型基线漂移、原厂资料/硬件缺口及HIL未闭环，未独立人工评审。review_round=1，review_mode=whole-change self-review，核对了默认优化恢复、用户态依赖移除、内核缺资源拒绝、静态包门禁、Camera/Display原生路径和失败批次边界。建议下一次完整构建使用新的.tmp/native-alignment-firmware-20261022目录，沿现有a123x-build.sh串行入口。
Codify Decision：reusable_pattern=新增外围沿SDK原生入口并由正确层级校验；promotion_candidate=false；next_task_friction_reduced=避免新增用户态假设改变SDK默认；reduced_by=静态包检查与内核故障注入；reduction_evidence=本轮回归及隔离构建；do_not_promote_reason=项目策略且缺设备验收；owner_review=pending；rollback_path=按本轮文件级增量回退，不能整体清理dirty；verification_evidence=上述结果。
