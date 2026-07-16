---
id: pcr02-module-clean-source-build-audit-20260715
title: PCR02 API/App/HDI/MP4 精确源码构建审计
kind: validation
domain: projects/xcrz-sigmastar-demo
path: projects/xcrz-sigmastar-demo/validation/2026-07-15-module-clean-source-build-audit.md
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
- clean-source
- validation
- build
- manual-validation-pending
related:
- projects/xcrz-sigmastar-demo/README.md
- indexes/obsidian-home.md
- indexes/project-readiness.md
validation_refs: []
artifact_refs: []
target_version: null
test_environment: null
summary_zh: 在精确组合源码、精确 SDK commit 与派生可迁移配置下复核 API/App/HDI/MP4 object build；API、App、MP4 返回 0，HDI 因 SDK 缺少 cam_dev_wrapper.h
  返回 2，四项证据契约均继续 pending。
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
- PCR02 API/App/HDI/MP4 精确源码构建审计
---

# PCR02 API/App/HDI/MP4 精确源码构建审计

## 验证目标

验证 PCR02 API、App、HDI、MP4 四个模块在以下约束同时成立时，能否从已登记的精确 Git commit 强制重新编译 object：

- `gros` 根仓、公共 AI 模块和四个目标模块均来自精确 commit 的隔离归档；
- PCR02 SDK 来自已登记精确 commit 的隔离归档；
- SDK 构建所需但未被 Git 跟踪的 `current.configs` 先绑定原始 SHA256，再只迁移四个构建根路径并绑定派生 SHA256；
- 通过 `NC=1` 禁止构建流程调用格式化器改写隔离源码，并通过 `make -B` 强制重新编译。

本报告只证明上述精确输入组合下四个 object build 命令的退出码和已观察 warning。它不证明构建环境完全由 Git 可复现、warning 已清零、链接产物正确、正式制品已生成、设备功能通过、版本已发布、回滚有效或 owner 已批准。

## 验证对象与输入身份

| 输入 | 精确身份 | 用途 |
|---|---|---|
| `gros` 根仓 | `899da6b5e1516a25df133435ce48f60082bc1b89` | 提供构建框架、公共目录和根级 Make 入口 |
| `modules/ai` | `716718fcbd8cba610cd8635f33f7fe5a9946ad65` | 四个模块的公共依赖 |
| `modules/api` | `3a7267485af998ef08ac2a9d256c37109f1f8bb7` | API 目标源码 |
| `modules/app` | `bec8700c5a9e9ddd382f4dbe0f049398dc76d8e0` | App 目标源码 |
| `modules/hdi` | `39e7dd2e204e91ea5d73b8da4860c33cf9a31d04` | HDI 目标源码 |
| `modules/mp4` | `d7c5cd855ec86b6d4fb0ccb3935f1ce486ae1ae7` | MP4 目标源码 |
| PCR02 SDK 根仓 | `cd03c7d59eeaf0d81432301ac2a457bb1bb48b2b` | 提供 `SourceCode`、交叉编译环境和 SDK 头文件/库 |
| 原始 `SourceCode/project/configs/current.configs` | SHA256 `23687bf8378205c614e49740428bb7d259585504659da3cd49b1c21f99da7890` | 本机构建配置；未被 SDK Git commit 跟踪，且含指回原工作区的绝对路径，因此不作为最终隔离构建证据 |
| 派生 `current.configs` | SHA256 `68bfe370ad9ad8af0c9228c448a6a022fb6cec9e969f1b1df7b3b0ecc19c23b1` | 仅把 `PROJ_ROOT`、`CLANG_TIDY`、`CLANG_FORMAT`、`KERNEL_ROOT` 四个路径迁移至精确 SDK 临时目录；是独立绑定、非 Git 输入 |

`gros` 精确根 commit 本身不跟踪本报告所列四个模块目录；因此隔离树是由上表各仓 commit 组合而成的复合快照，而不是把当前脏工作树复制后直接构建。复合关系已明确列出，不把它描述为单仓可复现快照。

## 环境与边界

- 日期：2026-07-15。
- 主机：Knowledge Hub 当前受控执行主机。
- 复合源码目录：`/tmp/kh-pcr02-composite-exact-20260715-1230`。
- SDK 隔离目录：`/tmp/kh-pcr02-sdk-exact-20260715-1255`。
- SDK 配置：原始配置含指回当前 SDK 工作区的绝对路径，不能证明隔离性；最终结果使用只迁移四个构建根路径的派生配置。两个版本均已单独绑定 SHA256，未把任一版本冒充为 Git commit 内容。
- 外部工具链：交叉编译器来自本机 `<local-pcr02-workspace>/.toolchains/ssc305/`；主机用户路径不进入长期正文。该工具链不属于 SDK commit 或 `gros` commit，故本报告不声明 hermetic build。
- 剩余路径边界：派生配置仍保留生成时写入的其他绝对表达式和 `PATH`；本轮 object 目标未调用其中的 image/mmap 生成入口，但尚未用系统调用追踪证明所有环境读取完全封闭。
- 构建模式：`NC=1` 禁用源码格式化，`make -B` 强制重新编译，`-j20` 并行。
- 写入边界：仅在 `/tmp` 隔离目录生成 object 和中间文件；未修改任何源项目已跟踪文件，未写 NAS、设备、发布系统或远端 Git。
- 证据保留：长期层只保存输入身份、命令、退出码、warning 分类和边界；临时 object、构建缓存与原始长日志不进入 Knowledge Hub。

## 验证命令

以下命令均以 `/tmp/kh-pcr02-composite-exact-20260715-1230` 为 cwd；公共环境把 `ALKAID_PATH`、`ALKAID_PROJ`、`ALKAID_PROJ_CONFIG`、`OUT_PATH`、`OUT_LIB_PATH` 和 `IMAGE_PATH` 指向两个 `/tmp` 精确组合目录，`NC=1`。

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash -lc '<公共环境>; make -B modules/api_obj_all -j20'` | 0 | API object 强制重编译完成；本次日志中 `warning:` 计数为 0。 | `/tmp/kh-cross-module-api-20260715.log` | Project / Tool | 临时 object；非正式 artifact |
| `rtk bash -lc '<公共环境>; make -B modules/app_obj_all -j20'` | 0 | App object 强制重编译完成；`warning:` 计数为 12。 | `/tmp/kh-cross-module-app-20260715.log` | Project / Tool | 临时 object；非正式 artifact |
| `rtk bash -lc '<公共环境>; make -B modules/hdi_obj_all -j20'` | 2 | HDI 编译失败；精确 SDK 头文件集合中缺少 `cam_dev_wrapper.h`，同时在失败前记录 73 个 warning。 | `/tmp/kh-cross-module-hdi-20260715.log` | Project / Tool | 未形成完整 object 集；非正式 artifact |
| `rtk bash -lc '<公共环境>; make -B -f build/build.mk MODULE_PATH=modules/mp4 MODULE_NAME=mp4 APP_MODULE=0 gen_obj -j20'` | 0 | MP4 object 强制重编译完成；`warning:` 计数为 34。 | `/tmp/kh-cross-module-mp4-20260715.log` | Project / Tool | 临时 object；非正式 artifact |

## 结果矩阵

| 模块 | 精确模块 commit | 强制 object build | Warning 状态 | 正式 artifact | 设备 | 发布/回滚 | 结论 |
|---|---|---|---|---|---|---|---|
| API | 已绑定 | 退出码 0 | 本次计数 0 | 未生成/未登记 | 未执行 | 未执行 | object 构建通过；契约仍 pending |
| App | 已绑定 | 退出码 0 | 12 个，需治理 | 未生成/未登记 | 未执行 | 未执行 | object 构建部分通过；契约仍 pending |
| HDI | 已绑定 | 退出码 2 | 失败前 73 个 | 未生成/未登记 | 未执行 | 未执行 | SDK 接口/头文件契约漂移，构建失败 |
| MP4 | 已绑定 | 退出码 0 | 34 个，含高风险类别 | 未生成/未登记 | 未执行 | 未执行 | object 构建部分通过；契约仍 pending |

## Warning 观察

退出码为 0 不等于源码质量门禁通过。本轮观察到的主要类别如下：

- API：本次派生配置复跑日志未出现编译器 `warning:`；这只表示该命令的当前告警计数为 0。
- App：不兼容函数指针、丢弃 `const`、未使用变量/函数、`snprintf` 潜在截断。
- HDI：在遇到缺失 `cam_dev_wrapper.h` 的 fatal error 前，已出现 SDK 类型不匹配、在 `void` 函数中返回值、隐式声明、非 `void` 路径无返回和未使用变量等 warning。
- MP4：`toupper`/`fabsf` 隐式声明、指针 signedness、指针宽度转换、非 `void` 路径无返回、offset 潜在未初始化、未使用变量。

其中隐式声明、指针宽度转换、非 `void` 路径无返回和潜在未初始化项可能影响运行时行为，后续不能只按“编译成功”关闭。

## 排除证据与失败边界

以下结果不计入最终通过证据，但用于解释复现边界：

- 首轮使用未迁移 `current.configs` 的四项构建虽然退出码均为 0，但配置中的 `PROJ_ROOT` 实际指回当前 SDK 工作区，依赖身份不精确，已从最终证据中排除。该轮 HDI 的“通过”不得继续引用。
- 迁移构建根路径并重跑后，HDI 稳定暴露 `cam_dev_wrapper.h` 缺失；本报告据此纠正先前结论，不用旧日志覆盖新反证。
- 在未提供 `current.configs` 时，API 构建因架构配置为空出现 `initializer element is not constant`；这说明该生成配置是实际必需输入，而不是可省略环境噪声。
- `current.configs` 不存在于 SDK commit，当前只能做到“原始内容 + 四路径派生内容双哈希绑定”，尚未做到“配置生成器或受治理来源可复现”。
- MP4 默认格式化入口因主机缺少 `/tools/bin/clang-13/clang-format` 而失败；最终 object build 使用 `NC=1` 绕过格式化步骤。因此本报告不声明默认完整门禁通过。
- `/tmp` 下产生的 object 和中间文件只是验证副产物，不登记为正式 artifact，也不作为 release evidence。

## 结论

本轮结论为“三项 object 构建通过、一项真实失败”：API、App、MP4 在精确组合源码、精确 SDK commit、双 SHA256 绑定配置和外部本机工具链下，强制 object build 返回 0；HDI 返回 2，直接阻塞项是精确 SDK 中缺少 `cam_dev_wrapper.h`。四项结果都可作为对应 validation contract 的真实验证引用，但 HDI 引用必须明确标记为失败，其他三项也只能标记为 object 层通过。

该结论仍有三个重要限制：一是 `current.configs` 缺少 Git 内来源或受治理生成链；二是交叉工具链是独立本机输入；三是默认 MP4 格式化门禁缺工具，且 App/HDI/MP4 存在需要修复的 warning。因此四个项目的 `evidence_contract.status` 继续保持 `pending`，不得据此推断 artifact、device、release、rollback 或 owner gate 已完成。

## 剩余风险与后续动作

```yaml
manual_validation_pending: true
manual_validation_reason: API/App/MP4 object build 已执行，HDI 已暴露精确 SDK 头文件契约失败；生成配置来源、外部工具链、默认格式化门禁、warning、正式制品、设备、发布和回滚均未闭环。
required_followup:
  - 将 current.configs 纳入受治理来源或提供可验证生成器，并重跑同一精确输入构建
  - 对齐 HDI 与 SDK 的 cam_dev_wrapper.h 接口版本后重跑 HDI object build
  - 恢复固定版本 clang-format，使默认构建/格式化入口可执行
  - 优先修复隐式声明、指针宽度转换、非 void 路径无返回和潜在未初始化 warning
  - 生成带 SHA256 与来源绑定的受控 artifact，并执行目标设备验证
  - 形成 release record 与可恢复 rollback drill 证据
owner: leiwenjun
review_after: 2026-10-15
```
