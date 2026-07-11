---
title: PCR02 项目调试工具入口
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-18
last_updated: 2026-07-02
tags: [pcr02, tools, debug, knowledge]
related: [project-build-and-deploy-guide.md, ../architecture/project-overview-design.md]
validation_refs: [../../tools/debug/project-knowledge-debug.sh, sources/pcr02-project-tools/README.md, artifacts/manifests/pcr02-retired-body-prune-20260625.jsonl]
---

# PCR02 项目调试工具入口

## 1. 目标

本手册定义当前项目如何使用已迁移到 Knowledge Hub 的 PCR02 调试工具说明和项目 wrapper。旧团队知识库路径只作为 retired origin provenance，不再作为当前知识入口。

## 2. 前置条件

若仍需运行源项目 wrapper，按源项目当前脚本和项目本地 `AGENTS.md` 执行；Knowledge Hub 不再提供或推荐旧团队知识库环境变量。

```bash
export KNOWLEDGE_HUB_HOME="$HOME/knowledge-hub"
```

默认项目参数：

```bash
export PROJECT_EXE="${PROJECT_EXE:-prog_pcr02}"
export PROJECT_APP_DIR="${PROJECT_APP_DIR:-out/arm/app}"
export PROJECT_SYSROOT="${PROJECT_SYSROOT:-out/arm/target}"
```

调用者显式传入 `--proc`、`--bin` 或 `--sysroot` 时，wrapper 不再注入对应默认值；`--name value` 与 `--name=value` 两种形式都会被规范化。

## 3. 入口命令

查看解析后的环境：

```bash
rtk bash tools/debug/project-knowledge-debug.sh env
```

采集运行期基线：

```bash
rtk bash tools/debug/project-knowledge-debug.sh runtime-baseline --duration 30 --out-dir /tmp/pcr02-runtime
```

采集媒体链路快照：

```bash
rtk bash tools/debug/project-knowledge-debug.sh media-snapshot --out-dir /tmp/pcr02-media
```

采集 AI Vision 证据包：

```bash
rtk bash tools/debug/project-knowledge-debug.sh ai-bundle --model model.bin --config app.yaml --out-dir /tmp/pcr02-ai
```

审计主程序依赖：

```bash
rtk bash tools/debug/project-knowledge-debug.sh audit-binary --out /tmp/pcr02-binary-deps.txt --allow-missing
```

崩溃 bundle 分诊：

```bash
rtk bash tools/debug/project-knowledge-debug.sh crash-triage --core out/arm/app/core-xxxx --out-dir /tmp/pcr02-crash
```

快速查看 core：

```bash
rtk bash tools/debug/project-knowledge-debug.sh core-fastpass --core out/arm/app/core-xxxx
```

校验 core 与二进制是否匹配：

```bash
rtk bash tools/debug/project-knowledge-debug.sh core-match --core out/arm/app/core-xxxx
```

## 4. PCR02 离线 Core GDB 选择

PCR02/SigmaStar SSC305 的 glibc ARM Linux core 默认使用以下交叉 GDB：

```bash
/tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-gdb
```

使用 GDB 前先确认该路径可执行，并确认它能读取 core 的 ARM registers。不要优先使用 `/usr/bin/gdb`、`arm-none-eabi-gdb` 或旧 `/opt/gcc-linaro.../arm-linux-gnueabihf-gdb`，这些候选在 PCR02 core 调试中可能出现 host/target ABI 不匹配、无法读取寄存器、缺少运行库或 DWARF 兼容性不足。

若用户在问题中给出 GDB 路径，以用户路径为硬约束；若该 GDB 启动失败或无法读取 core，需要先报告阻塞原因，再尝试替代路径。任何源码行级结论前，必须先完成 core、设备 `/customer/bin/prog_pcr02`、本地二进制、debug symbol 和关键 shared library 的 BuildID/MD5 匹配。

## 5. Hub 知识入口

- `domains/embedded/`
- `projects/pcr02/current/`
- `sources/pcr02-project-tools/README.md`
- 旧正文剪枝账本：`artifacts/manifests/pcr02-retired-body-prune-20260625.jsonl`

## 6. 边界

1. 项目 wrapper 只设置默认参数与调用入口。
2. 公共脚本增强必须先进入 Knowledge Hub source control 或对应源项目的明确变更流程；不得把旧团队知识库路径当作默认写入目标。
3. 现场日志、core 和大体积归档只能放 `/tmp`、受控 NAS 或问题单附件，不进入 Git。
4. wrapper 仅检查知识库目录和目标脚本是否可执行，不替代公共脚本自身参数校验。
