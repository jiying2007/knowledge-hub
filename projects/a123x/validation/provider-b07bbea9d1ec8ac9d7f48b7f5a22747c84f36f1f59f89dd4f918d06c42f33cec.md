---
id: provider-b07bbea9d1ec8ac9d7f48b7f5a22747c84f36f1f59f89dd4f918d06c42f33cec
title: A123X音频与传感器原生软件集成及离线验证
kind: validation
domain: projects/a123x
path: projects/a123x/validation/provider-b07bbea9d1ec8ac9d7f48b7f5a22747c84f36f1f59f89dd4f918d06c42f33cec.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: provider-candidate-archive
  from: operation:b07bbea9d1ec8ac9d7f48b7f5a22747c84f36f1f59f89dd4f918d06c42f33cec
  source_sha256: 60698e58a8dbf8f1031fbea2bd9ff23299535b8ed58cdc9eb963284aaecfa1ba
  temporary_source_retained: false
review_after: '2027-01-22'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- provider-archive
- validation
validation_refs:
- projects/a123x/validation/provider-b07bbea9d1ec8ac9d7f48b7f5a22747c84f36f1f59f89dd4f918d06c42f33cec.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/a123x/validation/provider-b07bbea9d1ec8ac9d7f48b7f5a22747c84f36f1f59f89dd4f918d06c42f33cec.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-10-24'
updated_at: '2026-10-24'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-10-24'
manual_validation_pending: true
summary_zh: 日期：2026-10-24（香港时间）。EV：EV-20261024-001。状态：reviewing / software-verified / board-not-run。 用户要求“音频 传感器等继续推进”，随后明确“和屏一样，先集成，后续再配io”。
  本记录只验收本轮软件接入；没有配置IO、访问目标板、刷写或提交推送。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
subject_ref:
  type: project
  id: a123x
created_subject_ref:
  type: project
  id: a123x
principal_id: local-user
provider_operation_id: b07bbea9d1ec8ac9d7f48b7f5a22747c84f36f1f59f89dd4f918d06c42f33cec
provenance:
  source_kind: session-conclusion
  source_ref: sanitized-conclusion
  verification_state: declared
aliases:
- A123X音频与传感器原生软件集成及离线验证
related:
- projects/a123x/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# 音频与传感器原生软件集成

日期：2026-10-24（香港时间）。EV：EV-20261024-001。状态：reviewing / software-verified / board-not-run。
用户要求“音频 传感器等继续推进”，随后明确“和屏一样，先集成，后续再配io”。
本记录只验收本轮软件接入；没有配置IO、访问目标板、刷写或提交推送。

## 已接入

| 能力 | 唯一源码责任 | 当前软件行为与边界 |
| --- | --- | --- |
| 原生音频 | SDK linux/mbp/tool/audio_pcm | 公开MBI/libmbi.a；PDM/TDM采集、AO0播放、S16LE、1/2个流声道、有限时收发、Get/Release配对和播放排空；不改变SYS/VBP、音量或功放，不等于四麦及D09采播参考通过 |
| QMI8658 | SDK platform/vendor/aml_commonlib/aml_sensors/qmi8658 | 独立库、ID、原始计数、设备tick、固定8g/1024dps/125Hz、已有active owner拒绝、退出恢复；无旧项目校准/中断/坐标策略 |
| VL53L8CX | 同包vl53l8cx | 内部HDI固定提交的ULD 2.0.0移植，显式Linux平台层、7/8位地址校验、分块读写、64区/10Hz诊断；无固定adapter、GPIO或工厂标定文件策略 |
| PMA2/F2C1 | 同包camsense | 接收解析库、分片/噪声重同步、校验、单位/位域转换、离线普通文件解码；不配置UART，不发送启停/标定/OTA命令 |

Kconfig分别为AML_AUDIO_PCM_DIAGNOSTICS、AML_SENSOR_QMI8658、AML_SENSOR_VL53L8CX、AML_SENSOR_CAMSENSE。
DEVWIRE显式选择；原厂CB400/EVT1配置测试保持关闭。不新增DTS/pinmux、电源/IRQ或开机服务。
实际运行前须由原生Kconfig更新选择；本轮隔离包构建使用显式选择，未改活动.config。

SDK原生vendor包为audio_pcm_diagnostics、motion_sensors，安装与build显式串联。
输出为audio-pcm、sensor-diag、camsense-decode及libqmi8658.so/libvl53l8cx.so/libcamsense.so。
三种CLI均有无设备访问的默认plan；后续运行及参数边界见各源码目录README和SDK调试导航。

## 来源与失败修正

内部参考仓modules/hdi固定提交d8a77053b38d00ebbe3276596e0f4833ade37633；只核对并读取对应驱动文件，未修改参考仓。
原始hash和协议PDF hash在SDK包source-lock.json。ST buffers.h字节保持一致；api.c/.h是明确移植版，
隔离旧HDI、旧唤醒和旧标定文件策略，保留版权头，补齐局部循环变量及结果长度/字段有效性检查。
它不是未经修改的ST官方新版本；来源缺独立LICENSE，额外分发资格须另审。

首轮Host链接失败暴露旧HDI依赖；修正后通过，不把失败日志改写成成功。协议参考为PMA2 V0.2
PDF第8–11页和F2C1 V1.0.5第9–11、18页。PMA2示例DN与描述矛盾，解析按字段定义和实际长度，
不复制矛盾示例。VI5300未取得适用来源，未增加占位驱动或虚构支持。

## 本轮验证

以下命令均经rtk执行，未执行ARM程序或设备操作。

| 命令/入口 | 结果 | 证据层 |
| --- | --- | --- |
| python3 -B -m unittest discover -s project/tools/codex_assets -p test_audio_sensors.py -v | 最后增量13项通过，exit0，7.407秒；含真实SDK头、Host/UBSan、初始化失败/信号/回收、现存文件保护、合作锁、独立安装、三板选择、关闭包和协议负例 | Host/SDK契约 |
| 同目录 -p 'test_*.py' -v | 85项通过，exit0，49.637秒；最后ToF字段有效性和音频取消阶段增量随后由上述专项复验 | 项目回归 |
| integration/scripts/a123x-check.sh --scope unit --require-complete | 196执行/通过，0跳过，67按scope排除，exit0，13.277秒 | 共享工具unit，不含SDK/HIL |
| 原生Makefile.vendor的audio_pcm_diagnostics-install motion_sensors-install | 从/tmp执行真实AArch64构建、严格链接和隔离安装，最终批次exit0 | SDK包构建/安装，非完整镜像 |
| 六个新ELF及递归依赖 | 六个均AArch64；使用既有SDK output target补足基础库，9个ELF依赖闭包通过 | ELF/既有依赖，非新镜像或板端ABI执行 |
| 活动.config前后hash | 均497393bed32bd344f43335a3e72bee1df3f06827a05786fd49f7cd879f5ed147 | 活动选择未切换 |
| project/scripts/validate.sh --metadata-only --dry-run | PASS；126任务、34需求/用例、7条EV；只核元数据，不核原件字节或设备 | 项目资料 |
| integration/scripts/a123x-docs-check.sh | 44份文档/168链接，problem_count=0；未查远端 | 本地文档 |
| test_evidence_registry.py | 新增第7条EV后发现原测试硬编码6条；改为与实际registry数量核对，6项复验通过，exit0 | 证据登记负例，非新增产品验收 |

最终隔离输出为本机临时目录`/tmp/a123x-audio-sensors-native-20261024-final/target`，不是长期发布契约。
来源和逐项产物hash见机器记录（来源内引用：`records/EV-20261024-001-audio-sensors.json`；尚未映射为 Hub 链接）。SDK三仓HEAD只作为提交基线，
dirty文件以机器记录中的实际hash为准；没有将本地候选宣称为远端固定可复现版本。

## 生命周期审查与后续IO

Review Target=本轮新增源码及共享构建/Kconfig对应hunk；Reviewer Independence=author-self-review。
已核对默认plan、唯一owner、部分初始化失败、Get/Release、信号、终止、文件/adapter锁、
停止/恢复错误传播、坏帧/截断与输入边界。独立reviewer/owner审查未发生。
不修改既有蓝牙、Wi-Fi和相机增量，不执行批量暂存。

后续依次确认音频物理麦数/路由与功放IO；QMI8658B版本/I2C/IRQ/坐标；ToF电源/复位/地址及实际
单/双器件拓扑；PMA2/F2C1 UART和启动控制。补四麦、采播参考/AEC、连续采样、测量精度、
断电恢复和并发HIL。原有D07/D08/D10/D11/D12/D18仅标in_progress；D09仍未验收。
源码接入、完整镜像、部署身份、设备结果和产品验收分开；本轮没有新USB/SWU整镜像或刷写结果。

## 收口与回退

Goal Claim=本轮可用来源的软件集成完成；Required Evidence=上述测试/交叉链接/隔离安装/来源hash。
Claimant=本线程；Verifier=实际命令、断言及逐文件/ELF核验；独立owner和主观听感/实物验证缺失。
Completion Guard只覆盖软件范围，不授予产品放行；Runtime最终门禁独立登记。
工具/权限/profile/标准变更、浏览器、模型trace eval均不适用；未引入外部服务或设备写通道。

Codify Decision：reusable_pattern=SDK原生包先集成后配IO；promotion_candidate=false；
next_task_friction_reduced=后续接线可复用同一录放/采样/解析入口；reduced_by=统一库/诊断/开关/安装责任；
reduction_evidence=13项专项、原生交叉安装与关闭功能负例；do_not_promote_reason=缺实物及独立owner审查；
owner_review=pending；rollback_path=按独立仓撤销本轮audio_pcm/aml_sensors及对应开关/包hunk，
保留既有dirty，成套重建；verification_evidence=本记录及机器hash记录。
