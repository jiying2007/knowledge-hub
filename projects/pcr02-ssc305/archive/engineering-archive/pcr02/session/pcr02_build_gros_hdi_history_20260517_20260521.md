---
title: PCR02 GROS、SSC305 build hardcut 与 HDI warning zero 历史归档 2026-05-17 至 2026-05-21
doc_type: project-archive
knowledge_type: historical-session
maturity: archived
status: archived
owner: leiwenjun
created: 2026-07-10
last_updated: 2026-07-10
tags: [pcr02, ssc305, gros, build, cmake, hdi, warning-zero, codex-archive-migration]
related:
  - ../source-audit/pcr02_imssv05c13_sdk_migration_plan_20260530.md
  - ../../../../current/runbooks/project-build-and-deploy-guide.md
  - ../../../../current/architecture/hdi-api-app-functional-overview.md
---

# PCR02 GROS、SSC305 build hardcut 与 HDI warning zero 历史归档 2026-05-17 至 2026-05-21

## 归档边界

- 状态：历史构建和会话归档，archive-only。
- 当前事实边界：本文只记录 2026-05-17 至 2026-05-21 的阶段性构建治理、GROS 试验和 HDI 编译告警收敛，不替代当前 PCR02 构建 runbook。
- 删除边界：旧 Codex archive 正文已在独立授权批次中删除；本文保留 source path、hash、风险和覆盖入口。
- 当前构建、发布和迁移口径以后续 PCR02 current runbook、IMSSV05C13 迁移归档和源项目实际脚本为准。

## 来源

| source_path | source_sha256 | size_bytes |
| --- | --- | ---: |
| `domains/codex/archive/codex-archive/session-wrap/20260517-154205-pcr02-gros-session-wrap.md` | `680438b0e528a0ccd7392e3b698983cfcec5cc1fefc0c27220dbd2783c13d6b4` | 5606 |
| `domains/codex/archive/codex-archive/session-wrap/20260518-223733-pcr02-ssc305-session-wrap.md` | `46a823463ea651802830f2c88eb29a3dfa6f4f1a96941633a2df43974d8d632f` | 4595 |
| `domains/codex/archive/codex-archive/session-wrap/20260521-091035-session-wrap-hdi-warning-zero.md` | `e33675294c1a583f4e51b787b71df19f475d51292beb65e29e0c1b95e77b14c9` | 1946 |

## 2026-05-17 GROS 构建试验

旧会话记录了 GROS 构建体系的一次阶段性收口：

- 根目录 `build.sh` 被设计为统一构建入口，覆盖 `full`、`compile`、`kernel`、`kernel-ota`、`kernel-package`、`ota`、`package`、`app`、`sysroot`、`self-check`、`verify`、`lock`、`modules-status` 和 `modules-sync`。
- GROS 应用构建切到 CMake，应用入口收敛到 `SourceCode/sdk/verify/gros/apps/pcr02`。
- 模块边界通过 `SourceCode/sdk/verify/gros/modules/repos.csv` 统一描述，支持 `repo`、`local`、`prebuilt`。
- 第三方依赖通过 `SourceCode/sdk/verify/gros/3rdparty/libs.csv` 统一描述 include、link path、link libraries 和 runtime dirs。
- 应用 sysroot 固化到 `SourceCode/sdk/verify/gros/sysroot/pcr02/ssc305`，并生成 `.sysroot.lock` 记录来源 SHA 与关键目录 hash。

该阶段验证过脚本语法、`generate-build-info.sh --self-check`、`modules-status`、`sysroot`、`self-check`、`verify`、`app`、`compile` 和 `ota`。但当时 root 仓与 GROS 子仓均有未提交改动，命令大量使用 `--allow-dirty`，不能作为发布级干净构建证据。

## 2026-05-18 SSC305 build hardcut

后一日旧会话记录主仓 `robot_pcr02` 分支完成并推送提交：

```text
fb5994d31 refactor(build): 统一构建与发布流程
```

该阶段把根 `build.sh` 固化为主构建入口，覆盖应用构建、系统镜像、OTA/SD 打包、自检、工具链检测、源码状态检查和模块命令。旧入口硬切，不再依赖 `compile_*.sh`、`release.sh`、`gen_version.sh`、`SourceCode/project/xcrz_env_set.sh` 和 `SourceCode/sdk/verify/makefile`。

关键边界：

- 普通构建当时优先选择 `xcrz_sigmastar_demo`，缺失时再使用 `gros`。
- `modules-status` 和 `modules-sync` 为 GROS 专用命令。
- 工具链不固化进主仓，使用本地 `.toolchains/` 承载外部工具链仓拉取结果。
- 自动化构建不隐式 checkout/pull；由 CI 或发布操作者先同步源码。
- 设备无 USB，因此不再生成 USB 工厂包，`--pack usb` 应失败。

验证摘要包括脚本语法、`build.sh self-check --allow-dirty --no-copy-nfs`、`git diff --check`、完整 `build.sh full --profile ap6303bh_512m_v20 --allow-dirty --no-copy-nfs`，以及 USB 负向验证。主仓最终干净并与远端同步，但嵌套应用仓仍有未提交变更。

## 2026-05-21 HDI warning zero

旧会话记录 `modules/hdi` 编译告警清零：

- 修复范围覆盖 `unused-variable`、`unused-function`、`unused-but-set-variable`、`format-truncation`、历史隐式声明和类型不匹配风险。
- 涉及 `hdi_disk.c`、`hdi_os_time.c`、`hdi_os_mem.c`、`ssplat_sys.c`、`hdi_vi.c`。
- 对 `hdi_disk.c` 的命令拼接缓冲区做统一扩容和保守构造，以降低 `-Wformat-truncation` 风险。
- 对调试或保留接口的未使用符号采用最小侵入处理。

验证命令口径：

```bash
rtk bash -lc 'make modules/hdi_obj_clean; make modules/hdi_obj_all -j20'
```

当时记录 `EXIT_CODE=0`、`WARN_COUNT=0`，并且 `/tmp/hdi_build.log` 中没有 `warning:` 或 `error:` 匹配。该记录只证明当时同口径构建通过，不代表当前 HDI 在所有工具链和 CI 环境下始终零 warning。

## 风险与保留限制

- 2026-05-17 GROS 记录是未提交工作区阶段性收口，不应升级为当前构建真相。
- 2026-05-18 build hardcut 对 2026-05-17 的 root `build.sh` 部分存在 supersede 关系，但 GROS/CMake/sysroot 线索仍保留历史价值。
- 当前 `project-build-and-deploy-guide.md` 可能不是同一时期 `build.sh` 口径；本文不替代 current runbook。
- HDI warning zero 是历史构建卫生证据，后续提交、产物、CI 和目标板验证仍需按当前项目流程确认。
- 本文不复制 raw build log、二进制、cache、工具链、完整会话或私有运行状态。
- 本文不写 memory、不提升 active、不生成 owner decision。

## 相关覆盖

- `projects/pcr02-ssc305/archive/engineering-archive/pcr02/source-audit/pcr02_imssv05c13_sdk_migration_plan_20260530.md`
- `projects/xcrz-sigmastar-demo/current/runbooks/project-build-and-deploy-guide.md`
- `projects/xcrz-sigmastar-demo/current/architecture/hdi-api-app-functional-overview.md`
- `projects/xcrz-sigmastar-demo/current/architecture/module-catalog.md`
- `artifacts/manifests/codex-archive-extract-first-preflight-20260710.jsonl#CAEF-20260710-021..023`

## 删除记录

旧 source 正文删除记录：

- `artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.jsonl#CARE-20260710-029`
- `artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.jsonl#CARE-20260710-030`
- `artifacts/manifests/codex-archive-removal-execution-20260710-pcr02-session-wrap-027-031.jsonl#CARE-20260710-031`
