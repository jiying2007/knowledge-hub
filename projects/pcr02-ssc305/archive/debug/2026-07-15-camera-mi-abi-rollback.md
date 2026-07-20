---
id: pcr02-camera-mi-abi-mix-rollback-20260715
title: PCR02 新摄像头栈混装 ABI 故障与回退记录
kind: debug-record
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/archive/debug/2026-07-15-camera-mi-abi-rollback.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: local-static-debug
  from: workspace://pcr02-ssc305
  source_sha256: b41a593df0ca570516609903b1e7d73a215dced411d23a4cedccccb0d70d7667
review_after: '2026-10-13'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02-ssc305
- camera
- mi-abi
- rollback
- sensor-mclk
validation_refs:
- projects/pcr02-ssc305/archive/debug/2026-07-15-camera-mi-abi-rollback.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: reviewing-validation-pending
evidence_refs:
- projects/pcr02-ssc305/archive/debug/2026-07-15-camera-mi-abi-rollback.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-15'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
manual_validation_pending: true
summary_zh: 确认新 sensor/vif/isp 与旧 common/sys 混装导致 MI 内部函数表错位；已回退 67 个摄像头移植文件并保留 Sensor MCLK DFS，待重新构建和板端启动验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 新摄像头栈混装 ABI 故障与回退记录

记录时间：2026-07-15（Asia/Hong_Kong）

状态：源码回退和静态验证完成；未重新编译，未生成新固件，未进行板端启动验证。

## 背景

为验证原厂 `Iford_IMSSV06C11_20260629` 中 AE/ISP 改善，曾向 `pcr02_ssc305_release` 定向移植摄像头用户库、公共头文件以及 glibc/uclibc 下的 `sensor.o`、`vif.o`、`isp.o`，同时单独移植 Sensor MCLK DFS 修复。

2026-07-15 生成的固件在启动时出现：

- `Segmentation fault`
- `insmod: can't insert '/config/modules/5.10/mi_vif.ko': Device or resource busy`

## 确认根因

故障固件把两代 MI 内核对象混装：

- `mi_common.ko`、`mi_sys.ko`：旧版 `project_commit.a70fe9c / sdk_commit.2e92c75`
- `mi_sensor.ko`、`mi_vif.ko`：新版 `project_commit.818dace / sdk_commit.7c86c02`
- `mi_isp.ko`：新 SDK 内的后续 ISP build `project_commit.758d3a1`

新旧 `g_mi_sys_internal_apis` 不是二进制兼容的尾部扩展：

- 旧版表大小 `0x170`；新版表大小 `0x188`。
- 偏移 `344/0x158` 在旧版是 `mi_sys_GetModParaInfoArray`，在新版是 `mi_sys_Debug_InitMod`。
- 新 `mi_sensor.o` 的必经初始化路径 `sensor__module_init -> MI_SENSOR_IMPL_Insmod -> _MI_SENSOR_IMPL_ModDbgParams_Init` 会调用该偏移。
- 新 `mi_vif.o` 初始化也会调用同一偏移。

因此，新 `sensor/vif/isp` 搭配旧 `common/sys` 会在模块初始化阶段调用错误函数。`g_mi_sys_internal_apis` 同时被 17 个 MI 对象使用，不能通过只补 `common/sys` 或改变装载顺序修复；保留新摄像头对象需要扩大到完整 MI 平台依赖闭包。

启动脚本 `SourceCode/project/image/output/customer/demo.sh` 第 19 行把 console printk 级别设置为 0，隐藏了 kernel oops；`mi_sensor` 和 `mi_vif` 分别在第 55、63 行装载。

## 本次处理决定

用户选择先执行恢复方案 A：

1. 回退本轮 48 个摄像头用户库。
2. 回退 13 个摄像头/ISP 公共头文件。
3. 回退 glibc/uclibc 下共 6 个 `sensor.o`、`vif.o`、`isp.o`。
4. 保留 `SourceCode/kernel/arch/arm/boot/dts/iford-clks.dtsi` 中 SR00～SR03 Sensor MCLK DFS 删除修复。
5. 不修改其他已有 dirty 文件，不修改应用 HDI 源码。

回退前确认上述 67 个文件全部仍与新 SDK 字节级一致，未发现用户在其上追加修改；随后定向恢复到当前仓库旧基线。

## 验证证据

- 回退范围：预期 67 个文件，回退后该范围 `remaining_dirty=0`。
- 与旧项目基线比较：`expected=67 exact_old=67 mismatch=0`。
- glibc/uclibc 的 `common/sys/sensor/vif/isp` 均恢复到 `project_commit.a70fe9c / sdk_commit.2e92c75 / sdklinux_commit.9e84084`。
- 恢复后的内部表大小：SYS `0x170`、Sensor `0xc4`、VIF `0x54`。
- `rtk git diff --check`：通过。
- `rtk bash -n build.sh`：通过。
- 按用户要求未执行编译。

## 重要边界

`SourceCode/project/image/output` 和 release module 目录属于忽略的构建生成物。11:40 失败构建留下的 `mi_sensor.ko`、`mi_vif.ko`、`mi_isp.ko` 仍是新版本，不能继续打包或刷机：

- 这些陈旧输出不代表源码回退失败。
- 必须重新完整构建，生成同一旧版 MI 内核模块后，才能进行板端启动验证。
- 在新构建和板端证据完成前，不得声明固件已可启动或可发布。

## 后续动作

1. 用回退后的源码重新完整构建固件。
2. 启动时确认 `mi_common/mi_sys/mi_sensor/mi_vif/mi_isp` build ID 属于同一旧基线，并确认不再出现 `Segmentation fault` 和 `mi_vif -EBUSY`。
3. 单独验证保留的 Sensor MCLK DFS 修复，不把它与新摄像头算法栈混为一个变量。
4. 若继续方案 B，应把任务升级为完整 MI 平台闭包迁移，至少覆盖全部 MI 对象、`sys/fb` 初始化层、`cam_os_wrapper`、MIU 以及用户态库/头文件闭包；不得再次只替换 camera 三对象。

## 结论边界

- “当前混装固件存在确定的 MI 内部 ABI 冲突”：已由对象 build ID、DWARF 表布局和初始化调用路径证明。
- “67 个摄像头移植文件已恢复到旧项目基线”：静态验证通过。
- “新固件已恢复启动”：未验证；缺重新构建和板端启动证据。
- “Sensor MCLK DFS 修复有效”：来源代码一致，但仍缺板端时钟和摄像头 A/B 验证。
