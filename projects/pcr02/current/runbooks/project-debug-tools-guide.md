---
title: PCR02 项目调试工具入口
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-18
last_updated: 2026-05-18
tags: [pcr02, tools, debug, knowledge]
related: [project-build-and-deploy-guide.md, ../architecture/project-overview-design.md]
validation_refs: [../../tools/debug/project-knowledge-debug.sh, $EMBEDDED_KNOWLEDGE_HOME/tools/debug/README.md]
---

# PCR02 项目调试工具入口

## 1. 目标

本手册定义当前项目如何使用团队知识库 `~/embedded/knowledge` 中的公共调试工具。当前项目只保留 wrapper 和项目默认参数，不复制公共工具实现。

## 2. 前置条件

建议设置：

```bash
export EMBEDDED_KNOWLEDGE_HOME="$HOME/embedded/knowledge"
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

## 4. 公共知识库入口

- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/core-dump-capture-guide.md`
- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/embedded-linux-performance-triage-guide.md`
- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/sigmastar-media-pipeline-triage-guide.md`
- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/yolo-ai-vision-deployment-guide.md`
- `$EMBEDDED_KNOWLEDGE_HOME/tools/debug/README.md`

## 5. 边界

1. 项目 wrapper 只设置默认参数与调用入口。
2. 公共脚本增强必须回到 `~/embedded/knowledge`。
3. 现场日志、core 和大体积归档只能放 `/tmp`、受控 NAS 或问题单附件，不进入 Git。
4. wrapper 仅检查知识库目录和目标脚本是否可执行，不替代公共脚本自身参数校验。
