---
id: pcr02-video-soak-memory-deadlock-20260813
title: PCR02 持续视频预览离线与内存池耗尽排障记录
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-08-13-pcr02-video-soak-memory-deadlock.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source:
  type: debug-session
  from: sanitized field-log summary, repository analysis, and local source-build evidence
  source_sha256: aba02ae0305bced3067a29b6189ffba1b1dc8e46bec4f40d289890a2fe7374b1
  temporary_source_retained: false
review_after: '2026-09-13'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- video
- memory
- deadlock
- debug
validation_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-13-pcr02-video-soak-memory-deadlock.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-08-13-pcr02-video-soak-memory-deadlock.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-13'
updated_at: '2026-08-13'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: codex-gpt-5
ai_generated_at: '2026-08-13'
manual_validation_pending: true
summary_zh: 持续视频预览离线的高置信候选为 VENC fd 泄漏与音频小对象积压共同施压，HDI realloc 另有确定自锁风险；源码已修复并构建，设备身份与实机长稳待确认。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# PCR02 持续视频预览离线与内存池耗尽排障记录

## 现象

- 设备在 APP 持续打开视频窗口约 15～20 分钟后离线，应用业务和显示画面停止更新。
- 两次已知异常分别发生在回充结束后静止场景和回充过程中；共同条件是持续视频预览。
- 串口证据在异常前出现大量固定内存池分配失败，脱敏统计共 2335 条，首条后迅速形成日志风暴。

## 影响范围

- 项目：PCR02 SigmaStar SSC305。
- 涉及模块：HDI 内存分配器、异步音频帧处理、VENC/VI 视频包生命周期、API 媒体环形缓冲与视频通道生命周期。
- 当前只完成源码静态分析、修复和主机交叉构建；设备实际制品身份及实机长稳尚未确认，不能据此宣布现场事故闭环。

## 环境

- ARM Linux / SigmaStar SSC305 源码构建环境。
- 输入证据为脱敏后的现场串口日志摘要、仓库源码和本地构建产物身份。
- 未在知识正文保存 raw log、设备端点、客户资料、SDK 原包或二进制。

## 时间线

| 时间 | 操作或观察 | 结果 |
| --- | --- | --- |
| 现场异常前 | APP 持续视频预览约 15～20 分钟 | APP 离线、显示停止更新 |
| 现场异常前后 | 固定内存池分配失败集中出现 | 形成高频错误输出，提示小块分配压力或生命周期异常 |
| 源码审查 | 检查 HDI realloc、音频任务队列、VENC/VI、API 环形缓冲 | 确认多项独立资源和生命周期缺陷 |
| 本地修复后 | 重编 HDI/API 对象、动态/静态库和 PCR02 应用 | 交叉构建通过；提交前空白与分层检查通过 |

## 证据

- 现场日志脱敏统计：固定池失败消息 2335 条；固定池失败后源码可能继续回退 TLSF/libc，因此该单一消息不能独立证明设备致死。
- HDI realloc 原实现持有全局非递归 mutex 后，在固定池分支再次进入公开 malloc/free 路径，存在确定的同锁自死锁条件；触发后所有共享该锁的分配和释放均可能阻塞。
- VENC 获取包路径在查询失败或零包时存在文件描述符未关闭路径，持续推流可积累资源泄漏。
- 音频采集每约 40ms 创建一次小型 OneShot 任务节点；原实现缺少有界背压和可靠退出清理。视频负载拖慢消费者时可形成约 32 字节级小对象持续积压，与固定块池压力机制吻合。
- 原代码还存在包数组上限/长度校验、失败回滚、borrowed echo 所有权、环形缓冲并发关闭、字符串 realloc/溢出等非首要但可触发泄漏、越界、UAF 或状态泄漏的风险。
- 修复后本地主产物身份：
  - `prog_pcr02`：MD5 `0301554803c6febb0ba415648c256552`，BuildID `cb46cb714b4f49ed8a02831b47855e2ab2cfd88e`
  - `libhdi.so`：MD5 `6b1a4f35dbfd9b3b385c51046c4cdd10`，BuildID `8c40de694e83854532b46d4297093c6de58d0e18`
  - `libapi.so`：MD5 `e663cf0a149dbbc09d400bcf669ae3a8`，BuildID `f6462a5c81afbe1b5b50d3ba5b504e3af91f9575`
- 一次负向门禁发现应用目标复用了旧 `libhdi/libapi`，其 MD5/BuildID 未变化；随后显式重建库并重新链接应用，避免把 stale 产物误报为已验证修复。

## 假设与排除

| 假设 | 验证动作 | 结果 | 状态 |
| --- | --- | --- | --- |
| 持续推流资源泄漏与音频小对象积压共同耗尽固定池 | 审查 VENC fd、音频 OneShot 节点和回收路径 | 找到确定缺陷及与现场时间尺度一致的压力机制 | 高置信候选，待实机验证 |
| HDI realloc 全局锁自锁导致各模块渐次停摆 | 审查 allocator 锁域和固定池 realloc 分支 | 找到确定的同锁嵌套调用 | 代码缺陷已确认，现场是否触发待证 |
| 回充或导航自身死锁 | 对比两次异常共同条件 | 一次发生在回充结束静止后，共同条件是持续视频预览 | 优先级低 |
| 单条 fixed pool full 足以证明致死 | 检查 allocator fallback | 失败后仍可回退 TLSF/libc | 已排除单条日志的充分性 |
| 当前本地源码与现场设备完全一致 | 比较证据级别 | 尚无设备 BuildID/MD5 | 未确认 |

## 根因

现场根因尚未最终确认。当前置信度排序如下：

1. 高：持续视频推流路径的 VENC 文件描述符泄漏，与音频异步小对象缺少有界背压共同造成资源和固定池压力；日志风暴进一步放大调度影响。
2. 中高：HDI allocator 的 realloc 确有全局非递归锁自锁条件；若现场触发，可解释内存相关模块及依赖模块渐次停摆。
3. 低：回充或导航自身死锁；两次事件缺少该共同条件。

最终定性必须先匹配现场 `prog_pcr02/libhdi.so/libapi.so` 的 MD5/BuildID，再完成视频预览与回充组合长稳验证。

## 修复或规避

- 将 allocator 拆成持锁内部 malloc/free helper，realloc 不再递归进入公开加锁接口；同时修复指针分类、calloc/realloc 溢出与失败保留旧指针、监控记录一致性、初始化/反初始化串行化。
- 固定池新增高水位、fallback、记录溢出和未跟踪释放计数；告警采用首次及 2 的幂次节流，并避免在 allocator 锁内输出日志。
- 音频 process/codec OneShot 任务启用显式、局部的事件合并上限，worker 批量排空；补齐 push 失败释放、退出广播、残留节点清理、帧状态回收和统计锁。
- VENC 所有返回路径关闭 fd，限制 pack 数并校验长度，确保 release；VI H26x 路径修正容量判断并在失败时释放包。
- API 环形缓冲补齐打开失败回滚、生命周期锁、reader 引用和 session 计数；视频通道打开改为事务式回滚；字符串工具补齐临时 realloc、自追加和整数溢出处理。
- 这些修改只修复源码。后编译 app/库不会自动进入既有 image 或 OTA，部署验证前必须重新生成相应制品并逐级核对身份。

## 验证

- `make modules/hdi_obj_all -j20`：通过。
- `make modules/api_obj_all -j20`：通过。
- `make modules/hdi_lib_all modules/api_lib_all -j20`：通过。
- `make pcr02_app_all -j20`：通过，且在显式重建库后重新链接。
- HDI/API 独立仓 `git diff --check`：通过；未出现文件模式漂移。
- 手工分层扫描未发现 HDI/API 反向依赖 app，也未发现诊断注册接口误入底层源码。
- 项目文档列出的三个自动诊断脚本在当前工作树不存在，不能声明这些脚本门禁通过；已用手工扫描作有限替代。

### 离线待验证

```yaml
manual_validation_pending: true
manual_validation_reason: 设备制品身份和现场视频/回充长稳未执行
required_followup: 匹配设备 MD5/BuildID，逐级执行视频预览 smoke、5～10 次短循环、1000 次长循环和 1～2 小时 soak
owner: leiwenjun
review_after: '2026-09-13'
```

## 后续动作

1. 冻结并核对设备安装态 `prog_pcr02/libhdi.so/libapi.so` 的 size、MD5、BuildID，身份不匹配时只保留函数/偏移级低置信分析。
2. 受控部署新制品后，按 smoke、5～10 次短循环、1000 次长循环、1～2 小时持续视频预览逐级放大；组合覆盖回充中、回充结束静止和普通静止场景。
3. 监控进程 fd 数、固定池高水位/fallback、OneShot 队列高水位/合并计数、进程和 ADB shell 健康、APP 在线状态及显示刷新；任一级出现 core、致命 dmesg 或状态泄漏即停止扩大。
4. HIL 闭环后再决定是否提升为 validation report；当前记录保持 reviewing，不提升为 active 事实。

## Provenance

- Captured: 2026-08-13
- Source: 脱敏现场日志摘要、当前源码静态分析、修复 diff 和本地交叉构建证据。
- Verification: 源码与构建门禁已完成；设备身份、部署和实机长稳待执行。
