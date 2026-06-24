---
title: SSC305 diag 与 prog_tool 回归方法
doc_type: runbook
knowledge_type: process
maturity: draft
status: active
owner: team-core
created: 2026-05-28
last_updated: 2026-05-28
tags: [ssc305, diag, prog-tool, regression, test]
related: [../standards/ssc305-feishu-knowledge-map.md, sigmastar-platform-development-workflow.md, embedded-build-reproducibility-guide.md, crash-triage-checklist.md]
validation_refs: [../archive/sigmastar/manifest.csv]
---

# SSC305 diag 与 prog_tool 回归方法

## 1. 目标

本文定义 SSC305 项目使用 `diag` 和 `prog_tool` 建立本地、远端、回归和现场复测闭环的方法。

适用场景：

1. 新增或修改设备侧诊断命令。
2. 构建后做 smoke 或回归。
3. 现场问题需要远端执行同一组命令复现。
4. 需要把人工测试步骤沉淀成可重复执行脚本。

## 2. 角色分工

| 工具 | 定位 |
| --- | --- |
| `prog_cli` | 人工交互、单命令调试、查看 help/catalog |
| `prog_tool run-cmd` | 单命令本地或远端执行，适合脚本和问题复现 |
| `prog_tool run <suite>` | suite 批量回归，适合 CI 或版本门禁 |
| `prog_tool session` | 多命令连续会话，适合 start/set/status/stop 闭环 |
| `tools/diag/diag-auto-run.sh` | 项目自动化入口，组合 precheck、strict 和 env |

## 3. local 与 remote 模式

| 模式 | 执行位置 | 适用场景 |
| --- | --- | --- |
| `local` | `prog_tool` 进程内拉起 diag runtime 和 providers | 单元/组件级验证、strict suite |
| `remote` | 通过 `cmd_server` 转发到运行中业务节点 | 全链路验证、现场联调、env suite |

判断规则：

1. local 失败、remote 正常：优先查本地依赖、provider up、工具初始化。
2. local 正常、remote 失败：优先查 `cmd_server`、IPC、目标进程、远端 registry。
3. 两者都失败：优先查命令实现、参数 schema、底层模块状态。

## 4. 最小回归顺序

设备侧建议顺序：

```bash
/customer/bin/prog_tool list
/customer/bin/prog_tool run strict --mode=local
/customer/bin/prog_tool run env --mode=remote --continue
```

项目自动化入口可封装为：

```bash
rtk bash tools/diag/diag-auto-run.sh --out-dir /tmp/ssc305-diag-auto
```

涉及构建时：

```bash
rtk bash tools/diag/diag-auto-run.sh --with-build --out-dir /tmp/ssc305-diag-auto-build
```

## 5. 单命令复现

先查帮助：

```bash
/customer/bin/prog_tool run-cmd diag.sys.help.run '{"command":"<diag.command>"}' --mode=local
```

再执行命令：

```bash
/customer/bin/prog_tool run-cmd <diag.command> '<json>' --mode=local --json
/customer/bin/prog_tool run-cmd <diag.command> '<json>' --mode=remote --json
```

单命令结论必须记录：

1. 命令名。
2. 参数 JSON。
3. mode。
4. `invoke_ret`。
5. 回复 JSON 的 `code` 和 `message`。
6. 是否可重复。

## 6. 会话脚本方法

适合播放器、录像、UART、OTA 等连续动作：

```text
# smoke.session
cmd run <start.command> {"arg":"value"}
cmd set <set.command> {"arg":"value"}
cmd status
cmd stop <stop.command> {}
quit
```

执行：

```bash
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/smoke.session --json
```

需要尽量收集更多失败时：

```bash
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/smoke.session --json --continue
```

## 7. suite 设计方法

| suite | 目标 | 命令选择 |
| --- | --- | --- |
| `strict` | 稳定门禁 | 低环境依赖、默认参数可稳定成功、要求 `code == 0` |
| `env` | 环境覆盖 | list/get/status/stop 等低风险命令，允许业务环境不满足 |
| `domain.strict` | 模块门禁 | 针对 hdi/api/app/core 某一层的强校验 |
| `domain.env` | 模块探测 | 针对某一层的可达性和状态覆盖 |

新增命令时至少考虑：

1. 是否能进入 strict。
2. 若不能进入 strict，是否能进入 env。
3. 是否有 help、summary、args_schema、example。
4. 失败返回码是否能区分参数错误、环境不满足和内部错误。

## 8. precheck 方法

新增或修改 diag 命令后至少检查：

```bash
rtk python3 tools/diag/checks/check_diag_metadata.py
rtk python3 tools/diag/checks/check_diag_command_quality.py
rtk python3 tools/diag/checks/check_diag_naming.py
rtk python3 tools/diag/checks/check_diag_interface_coverage.py
rtk python3 tools/diag/checks/check_diag_layer_deps.py
```

如果项目提供 case 矩阵，再检查矩阵同步：

```bash
rtk python3 tools/diag/checks/check_diag_case_matrix_sync.py
```

## 9. 常见失败路径

| 现象 | 定位 |
| --- | --- |
| `diag.sys.ping.run` 不通 | 查 `cmd_server`、IPC endpoint、目标进程 |
| `diag.sys.catalog.run` 无目标命令 | 查 registry 和 provider manager |
| `no_active_handler` | 查 provider 是否 up、命令 owner 是否注册 |
| local provider up 失败 | 查工具本地依赖、初始化参数、设备节点 |
| remote 超时 | 查业务进程阻塞、cmd_server 转发、IPC 堵塞 |
| env discovered 为 0 | 查远端发现链路，不应当直接视为通过 |

## 10. 收口标准

一次 diag/prog_tool 回归完成时至少输出：

```md
- firmware_version:
- tool_version:
- mode:
- suite:
- discovered:
- passed:
- failed:
- failed_cases:
- output_dir:
- blocking_issue:
```

没有执行回归时，不得声称“命令已通过”或“可合入”。
