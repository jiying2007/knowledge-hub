---
id: pcr02-aispeech-product-abi-20260921
title: AISpeech 产品 ABI 接入与构建阻断
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-product-abi-integration.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 03cb709f8fec09c76269b0e662edac5be0cf2781daf166c86f83c3b8b7f3c6a5
  temporary_source_retained: false
review_after: '2026-10-21'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-product-abi-integration.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-product-abi-integration.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 源码库和公开 ABI 验证通过，产品构建受跨子仓视频接口漂移阻断，VAD 事件生产未接通
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech 产品 ABI 接入与构建阻断

日期：2026-09-21。范围：本地源码、公开头、ARM 库和消费者验证。状态：部分完成，产品集成 blocked。未部署、未生成 image/OTA、未提交。

## 已落地

- PCR02 及共享第三方链接入口改为显式源码构建的 ARM AISpeech 静态库；源码缺失或 archive 缺失时失败，不回落旧 vendor 库。
- 根构建图补 AISpeech 依赖、公开头同步和 HDI/APP 依赖。pcr02 不再主动打包旧 AISpeech so。
- sevc_api.h 投影与源码一致；同步脚本增加 --header basename.h，仅同步 hdi_ai.h，保留 OS、VI、ToF 现有公开接口。
- app_test 迁移结构体事件回调，校验结构大小，并从真实概率字段读取 Q24。APP 当前分支已有结构体消费者；其源码在本轮外部切换，不计作本轮持久补丁。
- 新增 sevc_public_abi_smoke.c 和 run-public-abi，覆盖公开三参数 New、FeedPlanar、CALL 切换、状态、统计、EchoPathChange、Reset/Delete。

## 验证

- AISpeech ARM 静态库及动态库构建通过；公开 ABI 测试新 ARM 静态库链接通过，旧 vendor archive 因缺少新接口链接失败。ARM 程序未执行。
- Host 重建后 run-public-abi 通过。该测试使用投影公开头，不依赖私有结构。
- hdi_ai/hdi_ao ARM 对象成功编译；app_test 主文件 ARM 对象成功编译。
- 选择性同步 check、语法检查通过；非法路径返回 2、缺失头返回 1。
- HDI 全模块失败：hdi_vi.c:4556、4671 的回调调用仍为五参数，父仓公开类型要求六参数。
- APP 旧分支对象构建曾通过；外部切到当前分支后复验失败，涉及 VI 回调及 VSAPIRF_FrameNode_t/视频 reader API。旧通过不适用于当前 APP。
- OS、VI、ToF 公共头和 libhdi.a/libhdi.so 对比父仓 HEAD 均未改变；旧产品可执行文件未重生。

## 身份

- 父仓：3ea30b44bf26345767ef04eb9711e082174637a2，保留原有 dirty。
- AISpeech：9ce7a7f87b4835816e68df7fade6d43ebb3d47a1 加既有算法修复及本轮构建/测试改动。
- HDI：b34d16ccd732d23be766b9c2b2b05016ac877008，加单头同步 script.mk。
- APP 当前：0447b7dd898de5a1d6b46c60d1a2118dbbba50b4，dev/audio_process；执行期间从 master 4b2a317a2d99a680d2b78cb89d8775cbcdd21349 外部切换。
- API 当前：93c280695f9867030e7d8dc705d8d4dc3f346ba6，dev/audio_process。
- 新 ARM 静态库 SHA256：8433f5a2849cc9099a8f8f6721f40d1b569cf9551e0daa54ceb89ac97e318bc6。
- 新 ARM 动态库 SHA256：8b83e9204d5eff3c0a3a23c95f71f52e1fdaf1f5a1b7a7b20191b8ba97fcd555。
- sevc_api.h SHA256：deb90935403cd9192e7e879c09f2412d32bc5f9801a7054ff29689b5e013510d。

## 后续门禁

1. 冻结并对齐父仓公开接口与 APP/API/HDI 子仓源码组合，完成全产品链接、BuildID 和设备制品身份。
2. VAD 接入仍缺生产者：HDI _AI_SevcProcess 将 pbVadUpdated 保持 false，未填充 pstVadEvent；当前 SEVC 公共 API 无 VAD 导出。消费者类型一致不能证明事件已接通。
3. BF 关闭候选、NN/AGC/唤醒评估仍需设备耗时、声学和中文两词 HIL；本轮未改默认参数。

Runtime Control 返回 idle/no goal 的 required-artifact-missing，不替代上述真实构建结果；产品集成自身仍因源码接口漂移 blocked。
