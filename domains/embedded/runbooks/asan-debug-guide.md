---
doc_type: runbook
knowledge_type: debug-methodology
maturity: active
created: 2026-05-12
last_updated: 2026-06-29
related:
- asan-offline-symbolize-guide.md
- crash-triage-checklist.md
aliases:
- ASAN 调试方法论（团队级）
id: embedded-asan-debug-guide-20260629
title: ASAN 调试方法论（团队级）
kind: runbook
domain: embedded
path: domains/embedded/runbooks/asan-debug-guide.md
scope: team-general
visibility: team-internal
status: active
owner: team-core
source:
  type: hub-active-promotion
  source_manifest: artifacts/manifests/embedded-asan-active-promotion-20260629.jsonl
  provenance_manifest: artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl
  from: split-approved ASAN candidate rewritten without PCR02-specific paths; active promotion authorized on 2026-06-29; PCR02
    source path is evidence provenance, not active source binding
review_after: '2026-09-29'
review_status: human-reviewed-accepted
content_review_status: accepted
evidence_validation_status: verified
promotion: none
promotion_decision: active-team-runbook authorized for domains/embedded/runbooks only; promotion field remains none and does
  not authorize standards promotion, source project write, memory write or remote publish
tags:
- asan
- address-sanitizer
- memory
- debug
- methodology
- embedded
- team-runbook
validation_refs:
- domains/embedded/runbooks/asan-debug-guide.md
- domains/embedded/runbooks/asan-offline-symbolize-guide.md
- domains/embedded/runbooks/crash-triage-checklist.md
- domains/embedded/tools/debug/README.md
- artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl
- artifacts/manifests/embedded-asan-debug-guide-team-rewrite-20260629.jsonl
- artifacts/manifests/embedded-asan-team-owner-ready-package-20260629.jsonl
- artifacts/manifests/embedded-asan-active-promotion-20260629.jsonl
- registry/authorizations.jsonl
- rtk bash tools/knowledge-regression.sh --test test_embedded_asan_methodology_deprojectized --json
evidence_strength: user-authorization-plus-owner-decision-split-boundary-and-deprojectization-gate
evidence_refs:
- artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.jsonl
- artifacts/manifests/pcr02-asan-split-targets-20260618.md
- projects/xcrz-sigmastar-demo/current/runbooks/asan-debug-guide.md
- domains/embedded/runbooks/asan-debug-guide.md
- artifacts/manifests/embedded-asan-debug-guide-team-rewrite-20260629.jsonl
- artifacts/manifests/embedded-asan-team-owner-ready-package-20260629.jsonl
- artifacts/manifests/embedded-asan-active-promotion-20260629.jsonl
- registry/authorizations.jsonl
created_at: '2026-06-29'
updated_at: '2026-07-19'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-06-29'
summary_zh: 团队级 ASAN 调试方法论，已从 PCR02 project-local runbook 的 split-approved 边界中去项目化重写，并按 2026-06-29 用户明确授权提升为 active；项目命令和路径必须留在项目本地
  runbook，不提升到 embedded standards。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# ASAN 调试方法论（团队级）

## 1. 定位

本文是团队级 AddressSanitizer（ASAN）排障方法论，用于把不同项目里的内存越界、use-after-free、栈/堆破坏和相关崩溃收敛成同一套可复核流程。

本文只定义跨项目方法，不绑定具体芯片、产品、二进制名、构建变量、部署目录或动态库路径。项目里的 ASAN 开关、镜像布局、运行目录和库安装方式必须记录在项目本地 runbook 中。

项目特例参考：

- PCR02 项目本地 ASAN runbook：`projects/xcrz-sigmastar-demo/current/runbooks/asan-debug-guide.md`
- PCR02 owner decision 边界：`artifacts/manifests/pcr02-project-docs-owner-decision-landing-20260623.md`

上述 PCR02 文档只能作为项目特例参考，不作为团队默认命令或路径。

## 2. 适用条件

优先使用 ASAN 的场景：

- 崩溃点疑似来自内存越界、释放后使用、重复释放、栈破坏或堆元数据破坏。
- 普通 core dump 只能看到次生崩溃，无法定位首发写坏点。
- 问题可在 debug、diagnostic、SIL/HIL 或受控现场环境中复现。
- 目标系统有足够 RAM、存储和日志落盘空间承受 ASAN 运行时开销。

不适合直接使用 ASAN 的场景：

- 当前环境无法替换目标二进制或运行时库。
- 实时性、内存占用或 flash 余量对业务路径影响不可接受。
- 只能拿到 release stripped binary，且没有匹配符号、BuildID 或可复现路径。
- 目标问题是协议状态、设备时序、电源、文件系统损坏等非内存访问问题。

## 3. 开启前检查

每次开启 ASAN 前先确认四件事：

1. 构建系统能为目标模块追加 `-fsanitize=address`。
2. 编译时保留可回溯栈帧，至少包含 `-fno-omit-frame-pointer` 或等价 unwind 支持。
3. 目标运行环境能加载匹配的 ASAN runtime。
4. 产物和符号文件能通过 BuildID、版本号或制品 hash 对齐。

通用检查命令示例：

```bash
readelf -d <target-binary> | rg -i 'asan|sanitizer'
readelf -n <target-binary> | rg -i 'build.id|buildid'
```

如果 `readelf -d` 看不到 ASAN runtime 依赖，先回到构建配置确认 sanitizer flags 是否真正进入目标模块，而不是只进入了部分静态库或测试程序。

## 4. 运行期建议

首轮定位建议以“首发错误清晰”为目标，不追求一次收集所有问题。

推荐基础参数：

```bash
export ASAN_OPTIONS='abort_on_error=1:halt_on_error=1:detect_leaks=0:symbolize=1:log_path=<writable-log-prefix>'
```

参数取舍：

- `abort_on_error=1` 与 `halt_on_error=1`：首错即停，减少次生日志污染。
- `detect_leaks=0`：嵌入式现场优先定位越界和非法访问；泄漏检测可在资源允许时单独打开。
- `symbolize=1`：优先让 ASAN 输出函数名和源码行号。
- `log_path=<writable-log-prefix>`：把报告写入可持久化位置，避免串口、syslog 或 watchdog 截断。

如果目标机没有可用 symbolizer，可先保留原始 PC、SP、BuildID 和 ASAN 报告，再在主机侧离线符号化。

离线符号化参考：

- `domains/embedded/runbooks/asan-offline-symbolize-guide.md`
- `domains/embedded/tools/debug/README.md`

## 5. 标准定位流程

### Step 1: 固定首发错误

只以第一条 `ERROR: AddressSanitizer` 和第一段 `SUMMARY: AddressSanitizer` 为主证据。后续崩溃、断言、重启和 watchdog 日志通常是次生结果。

记录最小现场：

- ASAN 错误类型，例如 heap-buffer-overflow、stack-use-after-return、use-after-free。
- 访问方向和大小，例如 read/write、访问字节数。
- 首发栈帧 `#0` 到模块入口的最短调用链。
- 目标二进制 BuildID、构建版本、运行参数和复现步骤。

### Step 2: 校验符号匹配

定位前必须确认运行二进制和符号文件匹配。优先用 BuildID，其次用制品 hash、版本 manifest 或构建日志交叉确认。

```bash
readelf -n <runtime-binary> | rg -i 'build.id|buildid'
readelf -n <symbolized-binary> | rg -i 'build.id|buildid'
```

BuildID 不一致时，不得用当前源码行号直接下结论，只能把结果标记为“符号不匹配，需要重取制品”。

### Step 3: 收敛最小调用链

从 ASAN 报告中提取：

- 崩溃函数和源码行号。
- 直接调用者。
- 模块边界入口。
- 线程或任务入口。
- 触发输入、设备事件、协议包或定时器来源。

如果 ASAN 只给出地址没有行号，先检查 symbolizer、debug info、strip 行为和 BuildID，不要先改业务逻辑。

### Step 4: 判断错误类别

常见分类：

- 越界读写：优先检查数组长度、协议字段长度、DMA/缓冲区大小和字符串终止。
- use-after-free：优先检查对象生命周期、异步回调、跨线程 ownership 和失败路径释放顺序。
- double-free：优先检查错误处理分支、goto cleanup、引用计数和重复 close。
- stack-use-after-return：优先检查返回局部变量地址、延迟回调和栈上临时 buffer。
- global-buffer-overflow：优先检查静态表、枚举值范围和配置数组长度。

分类后只做最小修复，不在同一笔修复里重构无关路径。

### Step 5: 复现并回归

修复后至少保留三类证据：

- 同一路径复现不再出现原始 ASAN 报告。
- BuildID 或制品版本与修复构建一致。
- 没有新增更早的 ASAN 报告、启动失败或 watchdog 重启。

如果原问题依赖现场设备、时序或长时间运行，应记录复现窗口、运行时长和未覆盖风险。

## 6. 嵌入式注意事项

- ASAN 构建通常显著增加体积、内存占用和启动时间，不能默认进入 production 镜像。
- 运行时库部署必须与工具链 ABI 匹配；不匹配时可能表现为启动失败，而不是 ASAN 报告。
- 多线程系统中，首发 ASAN 报告比后续线程异常更可信。
- watchdog 可能截断 ASAN 报告；必要时使用 debug profile 或临时延长 watchdog 窗口，但必须记录回滚方式。
- stripped binary 只能用于运行，不适合作为符号化依据；保留未 strip 符号产物或独立 debug symbols。
- 现场日志中不得只保存截图；应保存原始 ASAN 文本、二进制版本、BuildID 和复现步骤。

## 7. 交付清单

ASAN 排障结论进入 Knowledge Hub 或项目 runbook 前，至少包含：

- 问题类型和首发 ASAN 摘要。
- 运行二进制与符号文件的匹配证据。
- 最小调用链和触发条件。
- 修复说明、复现结果和剩余风险。
- 项目本地命令、路径和镜像布局的引用，而不是写入团队级方法论正文。

团队级本文当前状态为 `active`。本次 active promotion 依据 2026-06-29 用户明确授权、去项目化检查和 Hub final gate 证据闭环；仍不得仅凭单一项目 owner decision 自动提升到 `domains/embedded/standards/`，也不得把项目本地命令、路径或二进制名写成团队默认。
