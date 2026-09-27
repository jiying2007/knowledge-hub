---
id: aispeech-board-sign-review-20260921
title: AISpeech ARM权重符号修复与板端恢复验证
kind: debug-record
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-board-sign-review.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: project-source
  from: workspace://xcrz-sigmastar-demo/modules/aispeech
  source_sha256: efba2edf04c85c73edec516d67dbe2e98671c01a19ffd0f08409a7a6eb5f4b62
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
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-board-sign-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- projects/xcrz-sigmastar-demo/archive/debug/2026-09-21-aispeech-board-sign-review.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-09-21'
updated_at: '2026-09-21'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-09-21'
manual_validation_pending: true
summary_zh: 板端复现修复NN权重符号缺陷，跨平台指纹一致，BF资源对照并恢复原应用
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
---

# AISpeech ARM板端验证与NN权重符号修复

用户授权使用当前设备端点，允许停应用运行测试。本轮仅暂存独立测试程序到设备/tmp，
未替换/customer/bin/prog_pcr02或设备库，未修改/data配置，没有重启设备。
端点与boot_id仅留在本次/tmp原始证据，本文不固化现场地址。

## 执行及恢复

首次ADB连接瞬时offline，随后只读devices确认device，重新preflight通过；不是长期失联或无限重试。
原应用有daemon双进程监护，daemon持有/dev/watchdog。采用SIGSTOP/CONT短暂停原应用，
保留监护/看门狗，逐批验证PID启动时间并设置有界超时和恢复guard。
首个smoke因目标BusyBox timeout语法不同未执行测试，立即恢复应用；确认timeout -t SECS后重跑通过。
不把旧ADB客户端的退出码当唯一成功证据，逐项解析CASE_RC、PASS及指纹输出。
正式批次前后均观察到应用T→S；最终同PID/启动时间、boot不变、原程序MD5不变。
原程序MD5 f57d7317e2753f99a06cb9e36b2b9dcc。
最终preflight为stable，core-hints为空，采样dmesg未匹配panic/Oops/BUG/segfault/OOM致命模式。
测试进程均退出，专用/tmp内18个本轮上传文件逐个清理，未动其他数据；本地制品保留。
MemAvailable清理前13236kB，清理后23460kB，接近初始23288kB。

原应用已恢复运行，但媒体NORMAL_30未独立量测，本轮没有改变媒体配置；不称完整媒体HIL闭环。
应用恢复后独立重查diag.hdi.ai.profile.get.run仍返回no_active_handler，不能取得应用内语音统计。

## 发现的确定性缺陷

最初ARM测试的INTERACTION指纹与Host一致，CALL不同。
原因：AISP_TSL_types.h中aisp_s8_t经S8别名成为plain char，FSMN nn_weight也直接用S8。
当前ARM编译默认plain char无符号，Host默认有符号，负量化权重解释不一致。
板端最小算术用例的raw bytes为80/ff/7f/01，输入2/3/4/5：
- 修复前权重128/255/127/1，逐项乘积256/765/508/5，点积1534，退出1，未崩溃。
- 正确权重-128/-1/127/1，乘积-256/-3/508/5，点积254。

最小修复：aisp_s8_t显式signed char，FSMN nn_weight使用aisp_s8_t。
保留S8字符串/字节接口，不全局改char编译开关，不改模型资源或参数。
类型宽度/结构布局不变，但所有依赖对象必须重编；这是修复数值语义，不是声学调参候选。
当前源码ARM构建已确认此问题；没有证明旧installed应用采用相同编译选项或同一库，
不得据此直接声称旧设备应用也存在该缺陷。

## 修复后板端结果

Host signed/unsigned-char两种编译下直接instrument nn_common.c，ASan/UBSan权重算术通过。
ARM板端负权重用例通过；修复后BF0/1均与Host固定输入指纹一致：
- 512帧INTERACTION：16040715878080958940。
- 512帧CALL：14346578963456371223。
- 1000帧混合模式/Reset：16985685392395738340。
未宣称所有输入、浮点/GRU配置或所有平台都已位级一致。
ARM VAD状态、NR/NN过渡/尾部排空/Reset、CALL Reset用例均PASS。
VAD全零256帧中237帧有效、170帧代理阳性，与Host一致；接口正确不等于校准语音检测器。
Host stage-contract、窗口与既有状态回归通过。源码diff --check通过。

## 修复后BF板端资源对照

修复前的性能结果不用于修复后结论。最终两版本同源，优化/PIC设置一致，BF独立切换；
80帧预热后每模式512帧，三轮交错顺序，对照期间应用暂停、daemon/watchdog及内核线程保留。
记录到CPU0频率1000000kHz，没有强制锁频/绑核；环境不是无后台负载实验室。

| 指标 | BF开启 | BF关闭 |
|---|---:|---:|
| ARM引擎申请内存bytes | 314516 | 307252 |
| INTERACTION线程CPU均值的三轮中位数us | 1470.082 | 1327.465 |
| CALL线程CPU均值的三轮中位数us | 3185.914 | 3025.309 |

引擎申请空间少7264B；线程CPU中位数分别少约9.70%和5.04%。不把该内存数称整进程RSS减少。
各轮输出指纹一致。12个模式结果里最大墙钟单帧约4916.333us，低于16ms帧周期。
这不覆盖AI采集、队列、网络、UI负载或扬声器，也不等于生产链截止时间保证。
BF默认仍开启；AGC及headroom候选默认仍关闭。

## 制品与限制

最终测试二进制均在push完成后核对本地/设备MD5；一次传输未结束时读到中间hash，
未运行该文件，等push完成后重新一致性检查再执行。
修复后默认ARM库和Host库已重建。最终ARM静态库SHA256：
af7f87d21d77ca6a58d43901796335ed6177f93d71426c7a3a5301bdfd6c06f5。
动态库SHA256：09f153891c9052b06ea3338c522813ebd2b17173a10ecd42c06baec9cb8c26fb。
最终BF1性能程序SHA256：e11424b57b8acee9cd5f82d60ebb2b5a39206b307aa09aa58f0fb5cc66f1ab4b。
最终BF0性能程序SHA256：6f5fde5c5ece6c1de3a77c38df9688c811c62cb2381573ac5ba1dd5119d7da2d。
本地制品/tmp/aispeech-board-bin-20260921；结构化结果/tmp/aispeech-board-results-20260921.json。
初始/最终只读证据分别在/tmp/aispeech-board-preflight-ready-20260921和/tmp/aispeech-board-final-preflight-20260921。
原始日志、设备地址、binary不进入Hub正文或Git；以上仅身份和结果摘要。

未执行真实麦克风/render同步、中文唤醒/通话听感或候选产品替换。原应用profile诊断不可用，
后续需解决产品集成/诊断接入后再做端到端声学验收。未commit/push/merge/image/OTA。
主代理自审，控制变量/失败复现/Host和板端对照为证据，无外部独立完整审查。
Runtime Control idle/null goal缺会话制品按planning skill单列not_applicable。
reusable_pattern: 固定点量化类型显式有符号，使用原始字节算术用例跨signed/unsigned-char及板端复现。
promotion_candidate: false；do_not_promote_reason: 项目特定证据与整机门禁未闭环；owner_review: pending。
rollback_path: 仅反向本轮数值类型补丁需重编库；设备原应用未替换无需回滚，暂停均已恢复。
next_task_friction_reduced: ARM权重算术和512帧可复跑；reduced_by: run-nn-weight-sign及平台化performance入口。
reduction_evidence: 1534→254负结果修复、跨平台指纹恢复、板端三轮和最终恢复检查。
