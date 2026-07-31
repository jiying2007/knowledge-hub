---
id: pcr02-vi-fps-code-quality-closeout-20260728
title: PCR02 1/30fps 代码规范收敛与板级复验
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-code-quality-closeout.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: agent-validation-summary
  from: xcrz_sigmastar_demo_dev
  source_sha256: a23f7d0bbc98042f602c65a15c0ea7c1d250db880b98b5c99a5e469ab7aeb7b9
  temporary_source_retained: false
review_after: '2026-08-28'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- validation
- vi
- 1fps
- 30fps
- code-review
validation_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-code-quality-closeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/validation/2026-07-28-vi-fps-code-quality-closeout.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-07-28'
updated_at: '2026-07-28'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-07-28'
manual_validation_pending: true
summary_zh: 1/30fps 切换代码完成跨模块规范收敛、主机与板级验证；形成未推送本地提交，仍需 owner 审查和远端分叉治理。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 1/30fps 代码规范收敛与板级复验
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# PCR02 1/30fps 代码规范收敛与板级复验

## 背景与范围

本轮针对 1fps/30fps 管线切换相关的近期提交进行跨仓库代码审查、规范收敛和板级复验。范围覆盖根工程、HDI、应用层、传感器策略、测试工具与诊断工具；未包含远端推送、合并或分支重写。

## 主要问题与修正

- 低帧率规划模型与真实 ISP/SCL 拓扑不一致：修正为 ISP port0 实时 SCL 链路。
- 规划器生成但运行期从不执行的 operation/action 列表造成伪契约：删除伪操作模型，规划结果只保留目标图与切换路由。
- WARM 与 HOT 路由语义混用：建立显式 COLD/WARM/HOT switch mode，公开路由固定为 COLD=5、WARM=6、HOT=1。
- 规划器遗漏 RAW YUV、JPEG、BMP 等需求：补齐节点、边、规格和 SCL1 独占冲突。
- 应用诊断 JSON 依赖超长 snprintf 与大量位置参数：改为有界 JSON writer，并按 graph、image、lifecycle、switch、timing 拆分。
- SDK 清理错误用按位或聚合，破坏首个错误码：改为保留首个错误。
- 补光策略在 mutex 内调用 HDI/ISP/IR 外部接口：将外部调用移到解锁后，由 worker 保证顺序。
- IQ 路径字符串存在并发读写风险：增加独立互斥与快照。
- 公共头文件同步脚本缺少只读校验且路径约束不足：增加 `--check`、模块名校验和 shellcheck。
- 测试工具使用魔法路由数字，诊断参数允许负数、溢出和尾随字符：改为公开枚举与严格数值解析。

## 验证结论

- HDI 管线单元测试与 sensor IR policy 单元测试均以 `-Wall -Wextra -Werror` 通过。
- HDI、app、sensor ARM 对象与库构建通过。
- app_test、app_tool、主应用 ARM 全量目标构建通过。
- 公共头文件只读同步校验、脚本 shellcheck、涉及文件格式校验、六个本地提交的 `git show --check` 均通过。
- 主机、共享发布目录与设备端测试程序哈希一致。
- 板级 COLD、WARM、HOT 双向切换均通过，无 PTS 回退；路由分别为 5、6、1。
- 参考板实测：
  - COLD：30→1 API 约 2.15s，1→30 API 约 3.36s，首个 RAW/主辅码流 IDR 最慢约 3.73s。
  - WARM：30→1 API 约 1.10s，1→30 API 约 2.21s，首帧/IDR 最慢约 2.61s。
  - HOT：30→1 API 约 0.46s，1→30 API 约 2.28s，首帧/IDR 最慢约 2.32s。
- 低功耗图确认 LDC、软光敏、VIF sleep 关闭，RAW/VENC 按需。
- 诊断工具本地会话 smoke 通过，未出现 JSON 截断或响应过大。

## 交付与边界

- 形成六个按模块拆分的本地提交，未 push、merge 或 rebase。
- 设计、计划、审查、状态与验证文档已在项目本地工作区更新；该目录按仓库约定被忽略，因此没有强制纳入提交。
- 构建生成库未提交，因为其依赖链包含用户原有未提交头文件，无法证明二进制只包含本轮变更。
- 根分支与远端存在双向分叉，后续推送前需要由维护者选择同步策略。
- 根工程格式化配置与当前工具链存在既有不兼容，且格式检查目标会修改源码；本轮没有提交格式配置漂移。
- 仍需模块 owner 进行人工审查；若进入发布，还需补充功耗、长稳和真实日夜/IR 场景回归。

## 可复用决策

1. 业务层只消费显式 COLD/WARM/HOT 路由契约，不依赖内部数字或伪 operation 序列。
2. HOT 只能在预检条件满足时启用，失败必须可回退到 WARM/COLD。
3. 切换性能应同时记录 API 返回、RAW 首帧、主辅码流首个 IDR 和 PTS 单调性。
4. 构建产物只有在依赖树可证明纯净时才可随源码提交。
5. 设备取证归档保留指标与判定，不归档私有端点、挂载路径或原始长日志。

## Provenance

- 日期：2026-07-28
- 来源：项目本地代码审查、主机测试、交叉编译与目标板硬件在环验证
- 生成方式：AI 辅助审查、实现与验证；需要人类维护者复核
