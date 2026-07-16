---
id: pcr02-robot-module-contract-audit-20260715
title: PCR02 Robot 子模块精确源码契约审计
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-15-robot-module-contract-audit.md
scope: project-specific
visibility: team-internal
status: reviewing
owner: leiwenjun
source: null
review_after: '2026-10-15'
created_at: null
updated_at: null
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- pcr02
- exact-source
- contract-audit
- validation
- manual-validation-pending
related:
- projects/xcrz-sigmastar-demo/validation/2026-07-15-module-clean-source-build-audit.md
- governance/product/validation/project-readiness.md
validation_refs:
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
artifact_refs: []
target_version: exact registered commits at 2026-07-15
test_environment: isolated composite source under /tmp with exact SDK commit, derived config and external local cross-toolchain
summary_zh: 以精确 commit、派生 SDK 配置和哈希绑定兼容 harness 复核 sensor、wifi、proto_c 及七个应用；仅 wifi 与四个应用的 object 层局部通过，其余暴露 schema、API、生成器、SDK
  库或头文件契约缺口。
review_status: human-reviewed-accepted
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: None
evidence_strength: null
evidence_refs: []
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-07-15'
human_reviewed_by: null
human_reviewed_at: null
review_basis: null
manual_validation_pending: true
aliases:
- PCR02 Robot 子模块精确源码契约审计
---

# PCR02 Robot 子模块精确源码契约审计

## 验证目标

在不修改任何源项目已跟踪文件的前提下，把 PCR02 Robot 根构建框架、子模块和应用的已登记精确 commit 组合到 `/tmp`，验证以下问题：

- `sensor`、`wifi`、`proto_c` 能否在精确根框架与精确 SDK 输入下重新生成或交叉编译；
- `daemon`、`cli`、`cmd_server`、`app_ota`、`app_product_test`、`app_tool`、`app_main` 能否完成交叉 object build 和最终链接；
- 失败究竟来自源码、proto schema、API、SDK 头文件/库，还是未受治理的根构建 harness；
- 各项目能否获得一个真实、可定位且不夸大的 validation contract 引用。

本报告不证明完整 root build 通过，不把临时 object 或 executable 当作正式 artifact，不证明设备功能、发布、回滚或真实采用，也不代替 owner decision。

## 验证对象

### 精确 Git 输入

| 项目 | 精确 commit |
|---|---|
| `xcrz-sigmastar-demo` / `gros` 根框架 | `899da6b5e1516a25df133435ce48f60082bc1b89` |
| `pcr02-sensor` | `36ec965dbdc16cdb8a8ad2b86132085f446964a4` |
| `pcr02-wifi` | `744a6d6dce06528a46ac54e5d5a3eed6e9b61038` |
| `pcr02-proto-c` | `9a63086e6e9d28885a5afaa08148ff7dea410cff` |
| `pcr02-daemon` | `6a0d646b63f9696a10500903e29c1d18034f883c` |
| `pcr02-cli` | `e1f9f38609b18b0ba7f7f30bb9a7a8deb29777ac` |
| `pcr02-cmd-server` | `3f7028a461cab5a7e29358949a9b21f342810a88` |
| `app-ota` | `d8242f101554f8e00e27dcd0137d10a367b081ac` |
| `app-product-test` | `c9eb16f59a2c1f3f0ec1149fb407bda999a4e47b` |
| `app-tool` | `c2d75b238bfadeea7d0730fbfef7daded33a0cf9` |
| `app-main` | `4adbf19f87d50d0635187126380b37fcefc0030f` |
| PCR02 SDK 根仓 | `cd03c7d59eeaf0d81432301ac2a457bb1bb48b2b` |

每个子仓均从对应精确 commit 取得，不使用源工作区未提交源码。`gros` 根 commit 不跟踪上述所有子仓，因此这里是显式复合快照，不是单仓 checkout。

### 非 Git、独立绑定输入

| 输入 | SHA256 | 边界 |
|---|---|---|
| 原始 `current.configs` | `23687bf8378205c614e49740428bb7d259585504659da3cd49b1c21f99da7890` | 含指回原 SDK 工作区的绝对路径，不计入最终隔离证据 |
| 四路径迁移后的 `current.configs` | `68bfe370ad9ad8af0c9228c448a6a022fb6cec9e969f1b1df7b3b0ecc19c23b1` | 只迁移 `PROJ_ROOT`、`CLANG_TIDY`、`CLANG_FORMAT`、`KERNEL_ROOT`；非 Git 输入 |
| `build/app_common.mk` | `2b100f45f4f06abb8b09d7b580162b062128aa5ee6b549fde060436e7875b029` | 原工作区未跟踪兼容 harness，仅用于把应用构建推进到源码/链接层 |
| `build/app_3rdparty.mk` | `e20c52fbfda0064151a404e6971a92a98e62359d3f67dc45534e4219e0828b33` | 同上，不冒充 `gros` commit 内容 |
| `build/app_sigmastar.mk` | `3ffb5d6b524afe67f462ede23a78f2e9a999d514926207bfae546da27c34a943` | 同上，不构成受治理正式构建入口 |

## 环境

- 日期：2026-07-15。
- 复合源码：`/tmp/kh-pcr02-composite-exact-20260715-1230`。
- 精确 SDK：`/tmp/kh-pcr02-sdk-exact-20260715-1255/SourceCode`。
- 派生 proto fresh clone：`/tmp/kh-pcr02-proto-c-fresh-20260715-1400`。
- 交叉工具链：本机 `<local-pcr02-workspace>/.toolchains/ssc305/`；主机用户路径不进入长期正文。这是独立环境输入，不属于上述 Git commit。
- 公共构建环境：`BUILD_TOP`、`ALKAID_PATH`、`ALKAID_PROJ`、`ALKAID_PROJ_CONFIG`、`OUT_PATH`、`OUT_LIB_PATH`、`IMAGE_PATH` 均指向 `/tmp` 组合目录；`NC=1` 禁用源码格式化写入，`make -B` 强制重编译。
- 所有生成文件、object、临时 executable 和原始日志均留在 `/tmp`，不进入长期文本知识层。
- 未连接目标设备，未读取正式 artifact store，未写 NAS、源项目、发布系统或远端 Git。

## 验证命令

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -lc '<公共环境>; make -B modules/sensor_obj_all -j20'` | 2 | `AudioPlay::STREAM_START` 与 `AudioCtrlPayload.scene()` 不存在；精确 sensor 与根 proto schema 不兼容。 | `/tmp/kh-cross-module-sensor-20260715.log` | Project / Tool | 无正式 artifact |
| `rtk bash -lc '<公共环境>; make -B -f build/build.mk MODULE_PATH=modules/wifi MODULE_NAME=wifi APP_MODULE=0 gen_obj -j20'` | 0 | 35 个源文件编译，记录 106 个 warning；含越界、截断、隐式声明和返回路径风险。 | `/tmp/kh-cross-direct-wifi-20260715.log` | Project / Tool | 临时 object |
| `rtk bash -lc 'git clone <exact-local-proto-c>; bash build_proto.sh <nanopb> <fresh> <fresh>'` | 0（错误返回） | `bridge_ctrl.proto` 报 `Missing numeric value for enum constant`，但脚本未传播失败并返回 0；未生成 `bridge_ctrl.pb.*`。 | `/tmp/kh-proto-c-generator-20260715.log` | Project / Tool | 忽略目录内生成源；非 artifact |
| `rtk bash -lc '<公共环境>; make -B -f build/build.mk MODULE_PATH=modules/proto_c MODULE_NAME=proto_c APP_MODULE=0 gen_obj -j20'` | 0（部分） | 只编译 `common.pb.c` 与 `nanopb.pb.c` 两个生成源，不能代表全部 proto 成功。 | `/tmp/kh-cross-direct-proto_c-20260715.log` | Project / Tool | 临时 object |
| `rtk bash -lc '<公共环境>; make -B ... MODULE_PATH=evidence/apps/daemon ... gen_obj; ... gen_exe'` | 0 / 2 | 4 个源码 object 可编译；链接缺 `-lcam_fs_wrapper`、`-lcam_os_wrapper`。 | `/tmp/kh-cross-obj-evidence_apps_daemon-20260715.log`、`/tmp/kh-cross-evidence_apps_daemon-20260715.log` | Project / Tool | 临时 object；无 executable |
| `rtk bash -lc '<公共环境>; make -B ... MODULE_PATH=evidence/apps/cli ... gen_exe'` | 2 | 编译期缺少 `CMD_SYS_EXEC_SHELL`。 | `/tmp/kh-cross-evidence_apps_cli-20260715.log` | Project / Tool | 无 artifact |
| `rtk bash -lc '<公共环境>; make -B ... MODULE_PATH=evidence/apps/cmd_server ... gen_exe'` | 2 | 编译期缺少 `CMD_SYS_EXEC_SHELL`，并有 HDI OS API 隐式声明。 | `/tmp/kh-cross-evidence_apps_cmd_server-20260715.log` | Project / Tool | 无 artifact |
| `rtk bash -lc '<公共环境>; make -B ... MODULE_PATH=evidence/apps/app_ota ... gen_obj; ... gen_exe'` | 0 / 2 | object 可编译且有 1 个隐式声明 warning；链接缺两个 SDK wrapper 库。 | `/tmp/kh-cross-obj-evidence_apps_app_ota-20260715.log`、`/tmp/kh-cross-evidence_apps_app_ota-20260715.log` | Project / Tool | 临时 object；无 executable |
| `rtk bash -lc '<公共环境>; make -B ... MODULE_PATH=evidence/apps/app_product_test ... gen_exe'` | 2 | 因 `proto_c` 未生成 `bridge_ctrl.pb.h`，首个源文件即编译失败。 | `/tmp/kh-cross-evidence_apps_app_product_test-20260715.log` | Project / Tool | 无 artifact |
| `rtk bash -lc '<公共环境>; make -B ... MODULE_PATH=evidence/app_tool/app_tool ... gen_obj; ... gen_exe'` | 0 / 2 | object 编译 0 warning；链接缺两个 SDK wrapper 库。 | `/tmp/kh-cross-obj-evidence_app_tool_app_tool-20260715.log`、`/tmp/kh-cross-evidence_app_tool_app_tool-20260715.log` | Project / Tool | 临时 object；无 executable |
| `rtk bash -lc '<公共环境>; make -B ... MODULE_PATH=evidence/app_main/app_tool ... gen_obj; ... gen_exe'` | 0 / 2 | object 可编译且有 1 个隐式声明 warning；链接缺两个 SDK wrapper 库。 | `/tmp/kh-cross-obj-evidence_app_main_app_tool-20260715.log`、`/tmp/kh-cross-evidence_app_main_app_tool-20260715.log` | Project / Tool | 临时 object；无 executable |

## 结果矩阵

| 项目 | object / generator | link | 主要阻塞 | 契约结论 |
|---|---|---|---|---|
| `xcrz-sigmastar-demo` | 分项执行，未形成完整 root pass | 未完成 | 独立子仓不在根 commit；兼容 harness 未治理；多项子契约失败 | validation 已发生，full integration 不 ready |
| `pcr02-sensor` | 失败 | 未执行 | sensor 与根 proto schema 漂移 | fail，继续 pending |
| `pcr02-wifi` | 返回 0，106 warning | 未执行 | 越界、格式、隐式声明等高风险 warning | object 层部分通过，继续 pending |
| `pcr02-proto-c` | 生成器假成功；仅 2 个源编译 | 未执行 | `bridge_ctrl.proto` 无效且脚本不传播错误 | fail/partial，继续 pending |
| `pcr02-daemon` | 返回 0，3 warning | 失败 | SDK wrapper 库缺失 | object 层部分通过，继续 pending |
| `pcr02-cli` | 失败 | 未执行 | `CMD_SYS_EXEC_SHELL` API 漂移 | fail，继续 pending |
| `pcr02-cmd-server` | 失败 | 未执行 | `CMD_SYS_EXEC_SHELL` API 漂移 | fail，继续 pending |
| `app-ota` | 返回 0，1 warning | 失败 | SDK wrapper 库缺失 | object 层部分通过，继续 pending |
| `app-product-test` | 失败 | 未执行 | 缺 `bridge_ctrl.pb.h` | fail，继续 pending |
| `app-tool` | 返回 0，0 warning | 失败 | SDK wrapper 库缺失 | object 层部分通过，继续 pending |
| `app-main` | 返回 0，1 warning | 失败 | SDK wrapper 库缺失 | object 层部分通过，继续 pending |

## 证据

- 精确 commit 通过各 `/tmp` clone 的 `git rev-parse HEAD` 复核；根框架来自 `899da6b...` 的精确归档。
- proto fresh clone HEAD 为 `9a63086...`；脚本输出明确包含 `bridge_ctrl.proto:25:13: Missing numeric value for enum constant.`，但 shell exit code 仍为 0，构成可复现的 false-success 缺陷。
- `wifi` 日志包括对 `cmd[CMD_MAX_LEN]` 的数组越界警告，以及多个 `snprintf` 截断风险；因此不能把 exit 0 当作质量门禁通过。
- 四个应用的 object 结果和 link 结果分开记录；缺失 SDK 库时不把 object pass 推导成 executable pass。
- 三个兼容 harness 文件只以 SHA256 绑定，不登记为 root commit 内容，也不作为长期正文副本保存。
- 原始日志属于临时执行证据；本报告保存可复用结论、输入身份、退出码和定位路径，不把 raw log 提升到长期知识层。

## 结论

本轮形成了 11 个项目的真实 validation 结果，但没有任何一个项目达到完整 evidence contract ready：

- `wifi`、`daemon`、`app_ota`、`app_tool`、`app_main` 只在 object 层局部通过；其中 `wifi` 有 106 个 warning，另外四项最终链接失败。
- `sensor`、`cli`、`cmd_server`、`app_product_test` 明确编译失败。
- `proto_c` 的生成脚本对实际错误返回 0，且 object 命令只覆盖两个生成源，属于假成功/部分编译。
- 根项目只提供精确构建框架；由于子仓组合、多项失败和未治理 harness，本轮不构成完整 root build 通过。

因此可以把本报告作为各项目 validation contract 的真实引用，但每个引用必须携带对应 `fail`、`partial` 或 `high-risk-warning` outcome，所有 `evidence_contract.status` 继续为 `pending`。

## 剩余风险

- `current.configs` 与三个应用 harness 均不是受治理 Git 输入；交叉工具链也来自本机外部路径，当前不是 hermetic build。
- SDK 精确快照缺少应用链接所需 wrapper 库，HDI 另有头文件缺口；需要先确认 SDK/source 版本矩阵。
- proto schema、生成器版本与错误传播逻辑未闭环，已直接阻断 sensor 与 product-test。
- `wifi` 的越界、截断、隐式声明、返回路径等 warning 可能转化为运行时缺陷。
- 没有正式 artifact SHA256、目标设备 run、release record、rollback drill 或真实采用反馈。
- 临时日志和 `/tmp` 产物不会长期保留；长期复现必须依赖本报告中的精确身份和重新执行命令。

## 后续动作

```yaml
manual_validation_pending: true
manual_validation_reason: 已完成精确源码交叉构建取证，但存在真实构建失败、未治理 harness、外部工具链、正式 artifact、设备、发布与回滚缺口。
required_followup:
  - 固化受治理的 root superproject、current.configs 生成链和应用 harness
  - 对齐 sensor/proto、cli/cmd_server API 与 SDK wrapper 头文件及库版本
  - 修复 proto_c build_proto.sh 的错误传播，并验证全部 proto 均生成和编译
  - 修复 wifi 高风险 warning，启用 warning-as-error 定向门禁
  - 生成 hash-bound 正式 artifact，执行设备、发布和回滚验证
owner: leiwenjun
review_after: 2026-10-15
```
