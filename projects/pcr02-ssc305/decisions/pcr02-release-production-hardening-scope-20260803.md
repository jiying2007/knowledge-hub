---
related:
- projects/pcr02-ssc305/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
decision_status: null
decision_date: null
id: pcr02-release-production-hardening-scope-20260803
title: PCR02 Release 生产化、安全与性能优化范围
kind: decision
domain: projects/pcr02-ssc305
path: projects/pcr02-ssc305/decisions/pcr02-release-production-hardening-scope-20260803.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: manual
  from: current-session-owner-request
  source_sha256: 7ce01cdbf3966fc66fbc75c3898372a31cc330dbd363f561e64b2c16eadeb1ed
review_after: '2026-11-03'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- release
- security
- boot-performance
- resource-optimization
- ota
- debug-release
validation_refs:
- projects/pcr02-ssc305/decisions/pcr02-release-production-hardening-scope-20260803.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/pcr02-ssc305/decisions/pcr02-release-production-hardening-scope-20260803.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-03'
updated_at: '2026-08-03'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-03'
manual_validation_pending: true
summary_zh: 定义 PCR02 Release 后续专项范围：逆向成本、敏感信息防泄露、运行时攻击面、OTA 与回滚安全、系统资源裁剪、启动加速及 debug/release 边界，并明确分阶段验收。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- PCR02 Release 生产化、安全与性能优化范围
---

# PCR02 Release 生产化、安全与性能优化范围

## 背景

PCR02 当前已形成量产 Release，后续工作不应只处理单点启动日志或编译开关，而应形成覆盖安全、性能、资源、升级和现场维护的生产化专项。既有排障已经确认网络能力、镜像内容和启动链配置会因 debug/release 差异产生真实运行影响，也确认 customer 静态 UBI 卷完整检查是当前启动路径中的显著耗时点。

本记录只固化工作范围、优先级和验收原则，不代表相关加固和优化已经实施或通过板端验证。

## 目标与非目标

目标：

- 降低开机动画、开机音频和应用可交互的用户可感知等待时间。
- 降低内核、rootfs、customer、常驻进程和运行日志的资源占用。
- 防止凭证、私钥、内部端点、源码路径和调试能力进入生产制品。
- 提高应用与系统被静态分析、动态调试和未授权修改的成本。
- 建立可追溯、可验签、可回滚、可诊断的 Release 和 OTA 交付链。
- 保持 debug 仅用于开发测试，量产设备只运行 release。

非目标：

- 不承诺通过混淆或 strip 完全阻止逆向。
- 不在缺少芯片能力和密钥基础设施验证时宣称已实现 Secure Boot。
- 不为了 debug/release 双向切换而立即统一 rootfs。
- 不以删除完整性校验、关键驱动或现场诊断能力作为启动和裁剪捷径。

## 适用范围

- 产品与平台：PCR02、SigmaStar SSC305、Linux 5.10 启动链。
- 层级：U-Boot、kernel、rootfs、customer/miservice、应用、OTA、发布制品和量产配置。
- 环境：开发测试设备的 debug 到 release 迁移，以及生产设备的 release 到 release 升级。
- 不适用：量产设备远程切换为 debug；该场景不在当前产品需求内。

## 权威来源

- source_id：manual current-session owner request
- source_path：PCR02 SSC305 当前工作区、启动分析和已有项目决策
- owner：leiwenjun
- source_status：reviewing，实施、量化基线和 HIL 验证待完成

## 工作包与优先级

### P0：敏感信息与发布安全

- 扫描源码、脚本、配置、rootfs/customer 和 ELF 字符串中的密钥、Token、密码、证书私钥、内部端点、构建机路径和调试账号。
- 生产包禁止携带私钥、明文长期凭证、core、map、未裁剪符号、测试脚本和开发配置。
- 日志不得输出认证材料、Wi-Fi 密码和完整设备唯一标识。
- 发布制品绑定 source commit、build type、配置、toolchain、分区 hash 和版本信息。
- OTA 在完整性 hash 之外引入发布者身份验证；签名、密钥轮换和设备端信任根另行设计验证。

### P1：逆向成本与运行时攻击面

- Release 评估启用优化、strip、独立内部符号、隐藏符号、栈保护、FORTIFY、PIE 和 RELRO/NOW；以工具链兼容和板端回归为准。
- 清理断言文本、源码绝对路径、调试菜单和内部协议说明。
- 限制 debugfs、ptrace、core dump、远程 shell、调试服务、敏感 proc/sys 节点、设备节点和非必要监听端口。
- 审查 U-Boot 控制台、启动倒计时、bootargs 和环境变量修改权限。
- 进程和文件权限遵循最小权限；不能用二进制混淆替代秘密管理。

### P1：启动加速

- 按上电到首帧动画、音频开始、应用可交互和网络可用四个节点记录 monotonic 时序。
- 优先处理 customer 静态 UBI 卷完整检查的显著耗时，同时保留或替换其完整性保证。
- 继续拆分 `/linuxrc` 中 UBI/UBIFS 挂载、mdev、sysctl、模块、firmware/config 和 launcher 时序。
- 将动画和音频的必要依赖前置，将 Wi-Fi、云服务、OTA 检查和非首屏业务异步或延后。
- 减少串行 shell、重复文件扫描、重复模块初始化和高频启动日志。

### P1：系统资源与镜像裁剪

- 建立 kernel、rootfs、customer、OTA 包大小和空闲/峰值内存基线。
- 记录 CMA/MMA、进程 PSS、线程数、CPU/I/O、模块、监听端口和日志带宽。
- 保留已确认必要的 IPv4、FUSE、Wi-Fi、音频、显示、媒体和 OTA 能力。
- 仅在依赖分析和板端回归后移除文件系统、协议、驱动、调试设施、命令行工具和后台服务。
- Release 降低 printk 和第三方驱动日志等级，同时保留脱敏故障码、版本和启动原因。

### P1：debug/release 与 OTA 边界

- 维持两套 rootfs：debug 仅开发测试，release 仅量产。
- debug 转 release 使用包含 kernel、rootfs、customer 和 miservice 的完整迁移包，避免混合系统。
- release 到 release 根据真实兼容性决定升级分区。
- 当前不加入跨 build type 的硬性拒绝门禁，可先采用 report-only 提示和发布清单审计。
- Release 构建不得携带 debug overlay、调试服务或开发工具。

### P1：可靠性与现场恢复

- 验证 OTA 断电恢复、失败回滚、降级策略以及 customer/data/factory 保留边界。
- 监控 NAND 坏块增长、UBI 剩余 PEB、文件系统只读降级、OOM 和关键进程退出。
- 明确 watchdog 与关键服务重启策略。
- 时间同步前同时记录 monotonic boot time，避免将 1970 年 wall clock 当作真实事件时间。

## 验收标准

| ID | 标准 | 验证方式 |
| --- | --- | --- |
| AC1 | 启动画面、音频、可交互和网络节点具有基线及优化后 P50/P95 数据 | 至少 10 次冷启动串口与 monotonic 打点 |
| AC2 | Release 制品无高危敏感信息命中 | 对 rootfs、customer、配置和 ELF 执行脱敏扫描并人工复核 |
| AC3 | 生产 ELF 不携带调试段和明显源码绝对路径，内部符号可定位崩溃 | `readelf`、`file`、`strings` 与内部符号回放 |
| AC4 | 无非必要监听端口、调试服务和可写调试入口 | 板端进程、端口、挂载、权限和内核配置审计 |
| AC5 | 资源优化有体积、内存、线程、CPU/I/O 前后对比 | 冷启动、空闲、业务峰值三阶段采样 |
| AC6 | 显示、音频、Wi-Fi、摄像头、AI、MCU 通信和 OTA 无回归 | 板端 smoke、长稳和关键业务回归 |
| AC7 | OTA 完整性、身份验证、断电恢复、回滚和数据保留闭环 | 制品审计、故障注入和真实设备演练 |

## 当前结论

Release 后续工作按本记录拆分为安全、启动、资源、构建边界和可靠性五条主线。逆向安全的目标是提高成本并减少泄露，不把秘密写入可提取制品；启动优化必须与完整性和稳定性一起验收。该结论当前为 `reviewing` 候选，尚未成为 active 发布规范。

## 生效条件

- owner 复核并签收范围与优先级。
- 建立当前 Release 的启动、资源、攻击面和敏感信息基线。
- 每个工作包形成独立实施方案、回退方式和板端验证证据。

## 回滚与变更条件

- 若某项编译加固导致工具链、第三方库或性能不可接受，按选项逐项回退，不整体关闭安全基线。
- 若静态 UBI 卷策略调整，必须先证明替代的 OTA 签名、写后校验和回滚机制有效。
- 若产品要求量产设备支持 debug/release 远程切换，重新评估统一 rootfs 和硬性 build-type 门禁。
- 芯片安全启动能力、分区布局或 OTA 架构变化时，由新决策 supersede 本记录。

## 风险与限制

- 逆向无法被完全阻止，混淆只能作为补充且可能增加体积、启动耗时和诊断难度。
- 当前 OTA 发布证据仍缺少完整的设备验收和回滚演练。
- 过度裁剪可能造成 Wi-Fi、FUSE、媒体或现场恢复能力回归。
- 原始串口日志、设备标识、内部服务地址、二进制和凭证未写入本记录。

## Review 周期

- owner：leiwenjun
- review_after：2026-11-03
- 下一次复核：基线结果、P0 信息泄露审计、启动 P50/P95、OTA 回滚和 debug 到 release 迁移验证。

## Archive evidence

- Source：当前会话中 owner 明确提出的 Release 专项范围。
- Captured at：2026-08-03 Asia/Hong_Kong。
- Sanitization：未保存 raw log、设备唯一标识、凭证、私有端点、二进制或 runtime state。
- Provenance：当前会话结论及 PCR02 已有 reviewing 决策与发布审计。
- Verification：Knowledge Hub transaction、全文检查和 governance dry-run。
- Memory Candidate：no；仅 reviewing decision candidate。
- Gate Result：needs-fix；本候选已完成登记与全文检查，全库 governance dry-run 被既有 Codex archive body-coverage 漂移和历史用户路径边界问题阻断。
