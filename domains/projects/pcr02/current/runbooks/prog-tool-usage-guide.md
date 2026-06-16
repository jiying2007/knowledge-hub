---
title: prog_tool 使用说明
doc_type: runbook
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-13
last_updated: 2026-05-14
tags: [diag, prog-tool, runbook]
related: [../reports/2026-05-14-prog-tool-terminal-release-report.md, examples/prog-tool-ci-smoke.session]
validation_refs: []
---

# prog_tool 使用说明（终态）

## 1. 工具定位

`prog_tool` 是基于 `diag` 命令体系的本地/远端统一测试执行器，用于替代旧 `app_tool` 的手工交互测试方式。

核心特性：

- 动态发现：运行时从 registry 或远端 `diag.sys.list.run` 自动发现命令。
- 动态组装用例：不依赖 `*.suite` 静态文件。
- 双模式执行：支持 `local`（进程内）和 `remote`（通过 `cmd_server`）。
- 双入口：既支持 suite 批量执行，也支持单命令执行。
- 统一结果：输出每个 case 的 PASS/FAIL 和最终 summary。

---

## 2. 产物与构建

- 目标产物：`/customer/bin/prog_tool`
- 构建目标：`make app_tool_app_all`

示例：

```bash
make app_tool_app_all -j8
```

---

## 3. 命令行接口

### 3.1 查看支持的 suite

```bash
/customer/bin/prog_tool list
```

输出固定包含：

- `core.strict` / `core.env`
- `hdi.strict` / `hdi.env`
- `api.strict` / `api.env`
- `app.strict` / `app.env`
- `strict` / `env` / `all`

### 3.2 运行 suite

```bash
/customer/bin/prog_tool run <suite> [--mode=local|remote] [--continue] [--json]
```

参数说明：

- `--mode=local`
  - 在 `prog_tool` 进程内启动 `APPDIAG` runtime，并 `ModuleUp` providers 后执行。
  - 命令发现来源：本地 registry（`VSAPPDIAG_RegistryCommandForEach`）。
  - 会按命令前缀自动准备本地依赖：
    - `diag.api.tick.*` -> 自动 `VSAPITICK_Init`
    - `diag.api.event.*` -> 自动 `VSAPIEVENT_Init`
    - `diag.app.uart.*` / `maint.app.uart.*` -> 自动 `VSAPPUART_Init`
- `--mode=remote`
  - 通过 `ipc:///tmp/cmd_server.ipc` 发送动态命令到运行中的业务节点。
  - 命令发现来源：`diag.sys.list.run` 的返回 JSON。
- `--continue`
  - 遇到 FAIL 不中断，继续执行后续 case；最终在 summary 汇总失败数。
- `--json`
  - 输出机器可解析结果：统一事件 schema（`run/run-cmd/session --script` 共用字段）。
- 每条 case 会额外输出一行结构化 JSON（含 `case_id/command/mode/expect/dep_ret/invoke_ret/reply_code/error_class/pass`），
  便于日志平台做自动统计与回归对比。

未指定 `--mode` 时默认 `local`。

### 3.3 执行单条命令（run-cmd）

```bash
/customer/bin/prog_tool run-cmd <diag.command> [json] [--mode=local|remote] [--hold-ms=<N>] [--json]
```

示例：

```bash
/customer/bin/prog_tool run-cmd diag.sys.ping.run '{}' --mode=remote
/customer/bin/prog_tool run-cmd diag.api.media.player.start.run '{"file":"/customer/res/test.wav","loop_times":1}' --mode=remote
/customer/bin/prog_tool run-cmd diag.api.media.player.start.run '{"file":"/customer/res/test.wav","loop_times":1}' --mode=local --hold-ms=5000
```

行为说明：

- 会先输出结构化执行结果（`trace_id/error_class/reply_code/reply_msg/invoke_ret/final_ret`）。
- 再输出原始命令回复 JSON（`run-cmd reply: ...`）。
- 进程退出码：回复 `code==0` 返回 `0`，否则返回 `-1`。
- `--hold-ms` 仅对 `run-cmd --mode=local` 生效，用于命令成功后保活一段时间（例如本地播放器播放 WAV）。
- `--json` 会隐藏 `run-cmd reply: ...` 的原始文本，仅保留结构化结果 JSON。

本地依赖说明：

- `run-cmd --mode=local` 会在执行前按命令域自动拉起依赖。
- UART 默认参数：`/dev/ttyS1, 115200, 8N1, flow=0`。

### 3.4 会话模式（session，推荐本地闭环控制）

```bash
/customer/bin/prog_tool session --mode=local
/customer/bin/prog_tool session --mode=remote
/customer/bin/prog_tool session --mode=remote --session-id=pt-session-001
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/player.session
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/player.session --json
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/player.session --json --continue
```

进入会话后支持：

- `cmd run <diag.command> [json]`
- `cmd set <diag.command> [json]`
- `cmd get <diag.command> [json]`
- `cmd stop <diag.command> [json]`
- `cmd status`
- `run <diag.command> [json]`（兼容写法）
- `help`
- `quit` / `exit`

示例（本地 WAV 闭环）：

```text
diagut> cmd run diag.api.media.player.start.run {"file":"/mnt/test.wav","loop_times":1}
diagut> cmd set diag.api.media.player.volume.set.run {"volume":70}
diagut> cmd status
diagut> cmd stop diag.api.media.player.stop.run {}
diagut> exit
```

说明：

- `session --mode=local` 是单进程闭环，适合 start/volume/stop 连续控制。
- `session --mode=remote` 通过 `cmd_server` 转发，适合全链路联调。
- 交互模式下，每次执行后会输出结构化结果 JSON（包含 `session_id/trace_id/mode/cmd/error_class/ok/ret/reply_code/reply_msg/elapsed_ms`）。
- `session --script=<file>` 支持批量回放会话命令（每行一条，支持 `#` 注释、`help`、`quit`）。
- `--json` 在 `session --script` 下生效；交互式 `session` 下会被忽略（避免影响人机交互）。
- `session --script` 默认 fail-fast：任一脚本行出错（含命令执行失败）立即退出并返回非 0。
- `session --script --continue`：失败后继续执行剩余行，最终返回最后一次失败码（或 0）。

脚本示例（`/customer/etc/diag_ut/player.session`）：

```text
# player smoke
cmd run diag.api.media.player.start.run {"file":"/mnt/test.wav","loop_times":1}
cmd set diag.api.media.player.volume.set.run {"volume":65}
cmd status
cmd stop diag.api.media.player.stop.run {}
quit
```

CI 用法示例：

```bash
# fail-fast（默认）
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/ci_smoke.session --json

# continue 模式（收集更多失败）
/customer/bin/prog_tool session --mode=remote --script=/customer/etc/diag_ut/ci_smoke.session --json --continue
```

`session --script --json` 统一事件 schema（固定字段）：

```json
{"schema_version":"diagut.v1","event":"session","type":"command","session_id":"sess-xxx","mode":"remote","line":3,"ret":0,"ok":1,"reason":"ok","cmd":"diag.sys.ping.run","suite":"","discovered":0,"passed":0,"failed":0,"suite_cases":0,"suite_passed":0,"suite_failed":0}
```

字段说明：

- `event`：固定为 `session`
- `schema_version`：事件协议版本（当前 `diagut.v1`）
- `type`：`start|script_start|command|status|help|line_error|script_abort|script_end|exit|parse_error`
- `session_id`：会话 ID
- `mode`：`local|remote`
- `line`：脚本行号（交互模式为 `0`）
- `ret`：该事件对应返回码
- `ok`：`1` 成功，`0` 失败
- `reason`：失败原因或语义标签（如 `command_failed`、`line_error`、`ok`）
- `cmd`：对应命令（无命令事件为空字符串）
- `suite/discovered/passed/failed`：`session` 事件下保留为统一字段（默认 `""/0/0/0`）
- `suite_cases/suite_passed/suite_failed`：suite 级统计字段；`session` 事件下默认 `0`

---

## 4. suite 语义

### 4.1 strict 套件

- 目标：稳定性门禁（回归硬门槛）。
- 行为：仅选择可稳定给默认参数的命令。
- 判定：要求返回 `code == 0`。

### 4.2 env 套件

- 目标：环境探测（连通性/可用性覆盖）。
- 行为：按模块挑选低风险命令，优先 `stop/get/list/status`。
- 判定：`expect=any`，允许业务返回非 0（如未初始化、无设备、环境不满足）。

### 4.3 聚合 suite

- `strict`：顺序执行 `core.strict -> hdi.strict -> api.strict -> app.strict`
- `env`：顺序执行 `core.env -> hdi.env -> api.env -> app.env`
- `all`：先跑全部 strict，再跑全部 env

---

## 5. 返回码与退出码

### 5.1 单条 case 判定

- `strict`
  - invoke 成功且 JSON `code` 等于预期（通常 0）时 PASS
  - 其他情况 FAIL
- `env`
  - 只要调用链可完成并拿到回复，都按 PASS 记录（用于环境覆盖）

case 结构化日志示例：

```json
{"case_id":"diag.api.tick.start.run","command":"diag.api.tick.start.run","mode":"local","expect":"eq","expect_code":0,"dep_ret":0,"invoke_ret":0,"reply_parse_ret":0,"reply_code":0,"error_class":"ok","ret":0,"pass":1}
```

`run --json` / `run-cmd --json` 统一事件示例：

```json
{"schema_version":"diagut.v1","event":"suite","type":"case","session_id":"","mode":"remote","line":0,"ret":0,"ok":1,"reason":"ok","cmd":"diag.sys.ping.run","suite":"core.strict","discovered":0,"passed":0,"failed":0,"suite_cases":0,"suite_passed":0,"suite_failed":0}
{"schema_version":"diagut.v1","event":"suite","type":"end","session_id":"","mode":"remote","line":0,"ret":0,"ok":1,"reason":"","cmd":"","suite":"core.strict","discovered":6,"passed":12,"failed":1,"suite_cases":6,"suite_passed":5,"suite_failed":1}
{"schema_version":"diagut.v1","event":"suite","type":"summary","session_id":"","mode":"remote","line":0,"ret":0,"ok":1,"reason":"","cmd":"","suite":"","discovered":107,"passed":28,"failed":0,"suite_cases":0,"suite_passed":0,"suite_failed":0}
```

说明：

- `type=end` 时，`suite_cases/suite_passed/suite_failed` 是该 suite 的增量统计。
- `type=summary` 时，`discovered/passed/failed` 是全局统计，不再复用 `line`。

### 5.2 进程退出码

- `0`：执行流程成功且 `failed=0`
- `-1`：参数错误、链路错误，或最终有失败 case

最终统一输出：

```text
=== summary === passed=<N> failed=<M> mode=<local|remote> discovered=<K>
```

---

## 6. 典型用法

### 6.1 本地快速回归（推荐开发阶段）

```bash
/customer/bin/prog_tool run strict --mode=local
```

### 6.2 本地全覆盖（不中断）

```bash
/customer/bin/prog_tool run all --mode=local --continue
```

### 6.3 联调链路验证（经 cmd_server）

```bash
/customer/bin/prog_tool run env --mode=remote --continue
```

### 6.4 单域排查

```bash
/customer/bin/prog_tool run api.env --mode=local --continue
/customer/bin/prog_tool run hdi.strict --mode=local
```

---

## 7. 常见现象与处理

### 7.1 `suite skipped: core.* (no discovered commands in current mode)`

含义：当前发现集合里没有该域命令，不是崩溃。

常见原因：

- local 模式下未注册 `diag.sys.*` 到本地 registry。
- remote 模式业务节点未上报对应命令。

处理建议：

1. 先执行 `/customer/bin/prog_cli diag list` 确认命令是否在线。
2. 再执行 `/customer/bin/prog_tool run <domain>.env --mode=remote --continue` 验证链路。

### 7.2 `Request timeout` 或 `route_timeout`（remote）

含义：`prog_tool -> cmd_server -> owner` 链路超时。

排查顺序：

1. 确认 `prog_cmd_server` 与业务进程均在运行。
2. 执行 `/customer/bin/prog_cli diag list` 看命令是否已注册。
3. 检查 owner 冲突或超时日志（如 `owner_conflict`、`node_timeout`）。

### 7.3 env 出现大量 ERROR 日志但 case 仍 PASS

含义：这是预期行为。`env` 用于探测覆盖，不要求命令成功完成业务动作。

建议：

- 关注 summary 的 `failed` 数；
- 对重点模块再补跑 strict 或定向 `/customer/bin/prog_cli diag run ...`。

---

## 8. 与 `prog_cli` 的关系

- `prog_cli`：人工交互与单命令调试（`diag list/run/catalog`）。
- `prog_tool`：自动批量执行与门禁统计（suite 级）+ 单命令执行（`run-cmd`）。

建议组合：

1. `/customer/bin/prog_cli diag list` 确认命令在线。
2. `/customer/bin/prog_tool run strict --mode=local` 做回归门禁。
3. `/customer/bin/prog_tool run env --mode=remote --continue` 做链路覆盖。

---

## 9. 终态约束（当前版本）

- 不再依赖 `app_tool/suites/*.suite`。
- 用例全部运行时动态生成。
- `prog_tool` 是 `app_tool` 重构后的唯一终态执行入口。
