---
id: gd32l235-charge-temperature-configurable-soft-hard-protection-20260812
title: GD32L235 可配置充电温度软硬保护策略决策候选
kind: decision
domain: projects/gd32l235
path: projects/gd32l235/decisions/charge-temperature-configurable-soft-hard-protection.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: working-tree-implementation-and-local-validation
  from: GD32L235 charge temperature working-tree implementation and local validation updated 2026-08-12
  source_sha256: 25675110ca74ea513a95dee23c057081c2722b9e8ed9459d63e3c842f6d05a29
  temporary_source_retained: false
review_after: '2026-09-12'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- gd32l235
- charge
- temperature-protection
- configurable-threshold
- hil-pending
validation_refs:
- projects/gd32l235/decisions/charge-temperature-configurable-soft-hard-protection.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/decisions/charge-temperature-configurable-soft-hard-protection.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-12'
updated_at: '2026-08-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-12'
manual_validation_pending: true
summary_zh: 普通充电的高温恢复值和软保护值可由0x37配置，分段确认区间随软门限平移，硬保护自动取软门限+3℃；软件门禁通过，实机热边界待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- GD32L235 可配置充电温度软硬保护策略决策候选
related:
- projects/gd32l235/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# GD32L235 可配置充电温度软硬保护策略决策候选

## 结论

普通充电 profile 采用可配置的高温策略。`0x37` 第 3/4 字节分别配置高温恢复值 `R` 和高温软保护值 `S`：

- `S`～`<S+1°C` 连续约 10 秒后停充；
- `S+1°C`～`<S+2°C` 连续约 5 秒后停充；
- `S+2°C`～`<S+3°C` 连续约 2 秒后停充；
- 软保护确认期间强制使用 1.25A 慢充，温度回落到 `S` 以下则取消本次确认；
- 任一有效温度样本达到 `S+3°C`，立即进入跨充电会话保持的硬保护；
- 软保护在温度不高于 `R` 连续约 30 秒后恢复；
- 硬保护在温度不高于 `R` 连续约 60 秒后恢复；
- 离桩清除软保护，不清除硬保护；温度无效或超过 10 秒未更新时禁止充电。

普通 profile 默认 `R/S=46/49°C`，因此默认硬保护为 52°C。`0x37` 的 4 字节帧布局不变，四个阈值必须严格递增；为保证派生硬保护不超过 85°C，普通 profile 的 `S` 最大为 82°C。认证 profile 保持第 3/4 字节作为直接恢复/保护阈值，不使用分段确认或 `+3°C` 硬保护。

## 背景与约束

设备运行逗宠、寻宠或回充等负载时，电池温度可能短时到达 49°C～52°C。第一次达到软门限即停充会放大瞬时波动并造成用户感知的频繁停充；单纯拉长软门限延时又可能削弱高温安全性。因此采用随温度升高缩短确认时间、软门限 `+3°C` 不经延时硬停的分层策略。

本轮不修改协议帧布局、固件版本或充电认证 profile。普通 profile 恢复 `0x37` 对高温参数的运行时配置能力，但不把软件构建等同于实机热安全验收。

## 实现边界

- 温度样本约每秒发布一次，以连续有效样本计数实现约 10/5/2 秒确认与约 30/60 秒恢复。
- `S+3°C` 硬保护优先于上/离桩会话判断，因此离桩也不能清除硬保护。
- 高温确认状态、软保护状态和硬保护状态可进入充电诊断日志，便于区分保护原因。
- 无效样本立即降为慢充并重新应用 PB10 温度门禁。

## 软件验证

已验证：

- 默认阈值与 45/48°C 平移阈值下的分段确认、温度回落取消、`S+3°C` 离桩硬保护、30/60 秒恢复和温度失效停充行为模型；
- 普通 profile 接受 82°C 软门限、拒绝会使硬保护超过 85°C 的 83°C 软门限；
- 普通 profile 全量仓库测试、fresh build、package 与 `fwtool check --scope all`；
- 认证 profile fresh build、merge、package 与 `fwtool check --scope all`；
- 普通 App 镜像 47104B，50KB 分区剩余 4096B，通过 4096B OTA 余量门禁；
- 认证 App 镜像 49632B，仍在 50KB 分区内，按既有 J-Link 非 OTA profile 规则豁免 OTA 余量。

负向证据：动态阈值首版使普通 App 只剩 4064B，并新增一条有/无符号比较告警，未通过构建门禁；改用相对软门限温差并压缩硬保护计数路径后关闭。更早的初版状态机余量门禁失败和认证版条件编译链接失败也均已关闭。

## 待验证与风险

真实硬件仍需完成：

1. 热箱或可控加热下验证默认 46/49°C 以及至少一组平移阈值的 `S/S+1/S+2/S+3°C` 边界、PB10、PA12 与温度日志时序；
2. 验证软保护离桩清除、硬保护跨会话保持及配置的 `R` 恢复时长；
3. 连续执行逗宠、寻宠、回充等高负载场景，确认减少软门限瞬时误停且 `S+3°C` 必停；
4. 检查传感器误差与板间离散性，不能用单台设备结果替代批量边界验收。

普通 App 的 OTA 余量正好等于 4096B 门禁，后续任何固件增长都可能重新触发门禁；不得降低门禁来掩盖增长。SOC 侧应继续发送原有 4 字节载荷，并把第 4 字节理解为软保护值；不需要新增硬保护字段。

## 来源与边界

- supersedes 候选：`gd32l235-charge-temperature-soft-hard-protection-20260812`；旧候选仍为 `reviewing`，需由 owner 复核后再决定是否正式标记 `superseded`
- captured_at：2026-08-12（Asia/Hong_Kong）
- last_verified：2026-08-12
- source：GD32L235 未提交工作树中的充电温控实现、自动化行为契约、普通/认证 profile 本地构建与制品检查摘要
- 排除：原始聊天记录、设备标识、完整构建日志、二进制制品、凭据和私有端点未写入正文
- Git 边界：工作树包含用户已有的 WiFi 相关改动；本候选仅记录充电温控决策，不声明已提交、已发布或已完成硬件验收
