---
id: gd32l235-charge-temperature-soft-hard-protection-20260812
title: GD32L235 充电温度软硬保护策略决策候选
kind: decision
domain: projects/gd32l235
path: projects/gd32l235/decisions/charge-temperature-soft-hard-protection.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: working-tree-implementation-and-local-validation
  from: GD32L235 charge temperature working-tree implementation and local validation captured 2026-08-12
  source_sha256: e82c7280a7a660f7ba3f7769ba9eed74057f39c7913272ffd13b3a93e9dae413
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
- hil-pending
validation_refs:
- projects/gd32l235/decisions/charge-temperature-soft-hard-protection.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/gd32l235/decisions/charge-temperature-soft-hard-protection.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-12'
updated_at: '2026-08-12'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-12'
manual_validation_pending: true
summary_zh: 普通充电采用49/50/51℃分段确认与52℃硬停，软硬保护分别在46℃连续约30/60秒恢复；软件门禁通过，实机热边界待验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- GD32L235 充电温度软硬保护策略决策候选
related:
- projects/gd32l235/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
---

# GD32L235 充电温度软硬保护策略决策候选

## 结论

普通充电 profile 固定采用以下高温策略：

- 49°C～<50°C 连续约 10 秒后停充；
- 50°C～<51°C 连续约 5 秒后停充；
- 51°C～<52°C 连续约 2 秒后停充；
- 软保护确认期间强制使用 1.25A 慢充，温度回落到 49°C 以下则取消本次确认；
- 任一有效温度样本达到 52°C，立即进入跨充电会话保持的硬保护；
- 软保护在温度不高于 46°C 连续约 30 秒后恢复；
- 硬保护在温度不高于 46°C 连续约 60 秒后恢复；
- 离桩清除软保护，不清除硬保护；温度无效或超过 10 秒未更新时禁止充电。

普通 profile 的高温恢复/软保护阈值固定为 46°C/49°C，`0x37` 不允许修改这两个值；低温保护参数仍沿用原配置接口。认证 profile 保持原有 43°C 停充、40°C 恢复的直接阈值策略。

## 背景与约束

设备运行逗宠、寻宠或回充等负载时，电池温度可能短时到达 49°C～52°C。第一次达到 49°C 即停充会放大瞬时波动并造成用户感知的频繁停充；单纯拉长 49°C 延时又可能削弱高温安全性。因此采用随温度升高缩短确认时间、52°C 不经延时硬停的分层策略。

本轮不提高 49°C 产品门限，不修改协议帧布局、固件版本或充电认证 profile，不把软件构建等同于实机热安全验收。

## 实现边界

- 温度样本约每秒发布一次，以连续有效样本计数实现约 10/5/2 秒确认与约 30/60 秒恢复。
- 52°C 硬保护优先于上/离桩会话判断，因此离桩也不能清除硬保护。
- 高温确认状态、软保护状态和硬保护状态可进入充电诊断日志，便于区分保护原因。
- 无效样本立即降为慢充并重新应用 PB10 温度门禁。

## 软件验证

已验证：

- 分段确认、温度回落取消、52°C 离桩硬保护、30/60 秒恢复、温度失效停充的行为模型测试；
- 普通 profile 全量仓库测试、fresh build、package 与 `fwtool check --scope all`；
- 认证 profile fresh build、merge、package 与 `fwtool check --scope all`；
- 普通 App 镜像 47096B，50KB 分区剩余 4104B，通过 4096B OTA 余量门禁；
- 认证 App 镜像 49636B，仍在 50KB 分区内，按既有 J-Link 非 OTA profile 规则豁免 OTA 余量。

负向证据：初版状态机使普通 App 只剩 3460B，未通过 4096B 余量门禁；压缩实现后关闭。认证版首轮因新鲜度函数条件编译范围错误链接失败，移至公共 profile 范围后关闭。

## 待验证与风险

真实硬件仍需完成：

1. 热箱或可控加热下验证 49/50/51/52°C 各边界的 PB10、PA12 与温度日志时序；
2. 验证软保护离桩清除、硬保护跨会话保持及 46°C 恢复时长；
3. 连续执行逗宠、寻宠、回充等高负载场景，确认减少 49°C 瞬时误停且 52°C 必停；
4. 检查传感器误差与板间离散性，不能用单台设备结果替代批量边界验收。

普通 App 的 OTA 余量仅比门禁多 8B，后续任何固件增长都可能重新触发门禁；不得降低 4096B 门禁来掩盖增长。若产品决定恢复普通 profile 高温阈值的运行时下调能力，需要重新评估代码体积并同步 `0x37` 兼容策略。

## 来源与边界

- captured_at：2026-08-12（Asia/Hong_Kong）
- last_verified：2026-08-12
- source：GD32L235 未提交工作树中的充电温控实现、自动化行为契约、普通/认证 profile 本地构建与制品检查摘要
- 排除：原始聊天记录、设备标识、完整构建日志、二进制制品、凭据和私有端点未写入正文
- Git 边界：工作树包含用户已有的 WiFi 相关改动；本候选仅记录充电温控决策，不声明已提交、已发布或已完成硬件验收
