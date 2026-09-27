---
id: pcr02-aispeech-nr-numeric-review-20260920
title: AISpeech NR 数值边界修复与声学门禁复核
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-nr-numeric-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: 1f51e246a72bd1e657f9c80602b06540313dd8560e27c9e1206fa915187cfc68
  temporary_source_retained: false
review_after: '2026-10-20'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- aispeech
- validation
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-nr-numeric-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-20-aispeech-nr-numeric-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-20'
updated_at: '2026-09-20'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-20'
manual_validation_pending: true
summary_zh: 修复NR定点功率溢出和谱减增益回绕，四分支UBSan通过；两场景既有声学门禁失败且与本轮修改无关。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech NR 定点边界修复与现有声学门禁

- captured_at / last_verified: 2026-09-20
- Source: workspace://xcrz-sigmastar-demo/modules/aispeech
- Review Target: working-tree，基于 HEAD 9ce7a7f87b4835816e68df7fade6d43ebb3d47a1
- Reviewer Independence: author-self-review；本记录不是独立审查或产品验收。
- 范围：NR 定点运算、当前 AEC 通道/Reset 修复的定向复验、尾链回归。
- 既有未提交改动保留；本轮新增仅为 NR 数值边界处理、数值测试、Makefile 入口和 README 说明。

## 已复现并修复

1. NR 复数功率在 S64 相加或收窄为 S32 时溢出。S32 最大值的实部/虚部可令首帧功率为负；两分量同时为 S32 最小值时 UBSan 捕获有符号加法溢出。改为 U64 累加、右移至 Q14 后饱和至 S32。此为频谱边界注入，未证明设备 PCM 会触发。
2. 非对称谱减的偏置噪声和负增益在限幅前收窄，导致突发信号后的增益误开。频谱幅度 1500000 的用例在第 15 帧应为 Q20 786432，却得到 1048576。传统谱减还存在满功率加 1 的 S32 溢出。改为保持 S64 至最终限幅。

未改变默认参数、公共 API、状态结构或内存分配。本轮不是新参数寻优。

## 新鲜验证

- `rtk make -C modules/aispeech/tests run-nr-numeric run-nr-state run-nr-shared run-aec-channel run-reset-equivalence run-long run-activity-dtd` 返回 0。
- 新增 numeric 测试对默认 DD、传统谱减、非对称谱减、非对称加 DD 四分支编译 NR 源码并启用 UBSan；其他库模块未插桩。
- 默认配置的 3 组非溢出输入，修复前/后输出及状态指纹均为 9975498722465419352；覆盖面有限，不替代声学验证。
- 1000 轮切换基线：40013 回调、2000 次切换、315604 bytes 内存；修改后同目标通过。
- SigmaStar glibc GCC 11.1.0 对 NR 源码的 ARM 定向对象编译通过；未重建产品固件，未部署设备。
- 子仓 `git diff --check` 通过。Host 全库构建仍有既有宏重定义和未使用变量告警。

## 声学门禁仍失败

使用 tests/Makefile 中 run-aec-quality 的两组 SLR28 RIR/noise 输入；评估器与当前 Host 静态库重新链接。
为区分本轮回归，在临时目录从最终 NR 源码逆向移除本轮数值补丁，保留原有用户修复，并直接链接该 NR 实现作为修改前对照。两组所有非计时 JSON 字段均一致。

| 场景 | 远端 ERLE dB | DTD 误激活率 | 削波数 | 修复前/后退出码 |
| --- | --- | --- | --- | --- |
| development Room001 | -0.225 | 0.06164 | 0 | 1 / 1 |
| validation Room002 | 22.533 | 0.06849 | 0 | 1 / 1 |

门限为远端 ERLE >= 0 dB，DTD 误激活率 <= 0.05。未放宽门限；未将 report-only 当通过。
当前结论：定向数值缺陷已修复，整体声学质量 needs-fix，SSC305/QIVW/HIL 未验证。
下一步应单独冻结 DTD 误激活及双讲结束后的恢复问题，核验评分窗口与算法行为，再做候选比较。

## 快照

- sevc/src/sevc_nr.c SHA256: 24fb3a6cda025e40f8f0a00622ddb1dcf7a159113bb850c49e4088005e921455
- tests/sevc_nr_numeric_regression.c SHA256: 9bdd7871f71ce046295638d310d8573f8140b079142b5445cfda51ba3b05307c
- tests/Makefile SHA256: 1e75e867af9ced7f9d10146e83a5f9acb6a3fa11e468808521e6112107a859dd
- Host libaispeech.a SHA256: 526197cb3b3bffd20d38ea45cbddc914bc998e1940be413fef75c58d92191ad8
- ARM NR object SHA256: 4438912997416c93031785e862c5173905c943c77dd133efb9199aac410a3827

仅保留脱敏结论与复跑入口，不包含音频、原始日志、设备端点或凭据；不晋升 memory 或团队规则。
