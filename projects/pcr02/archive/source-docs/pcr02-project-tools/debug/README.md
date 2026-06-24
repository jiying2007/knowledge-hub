# 项目 Debug 工具入口

## 入口脚本

- `project-knowledge-debug.sh`：封装团队知识库 debug 工具，并注入 PCR02 项目默认路径。

## 默认变量

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `EMBEDDED_KNOWLEDGE_HOME` | `$HOME/embedded/knowledge` | 团队知识库路径 |
| `PROJECT_EXE` | `prog_pcr02` | 默认目标进程 |
| `PROJECT_APP_DIR` | `out/arm/app` | 默认应用产物目录 |
| `PROJECT_SYSROOT` | `out/arm/target` | 默认目标 sysroot |

调用者显式传入 `--proc`、`--bin` 或 `--sysroot` 时，wrapper 不再注入对应默认值；`--name value` 与 `--name=value` 两种形式都会被规范化。

## 常用命令

```bash
rtk bash tools/debug/project-knowledge-debug.sh env
rtk bash tools/debug/project-knowledge-debug.sh runtime-baseline --duration 30 --out-dir /tmp/pcr02-runtime
rtk bash tools/debug/project-knowledge-debug.sh media-snapshot --out-dir /tmp/pcr02-media
rtk bash tools/debug/project-knowledge-debug.sh ai-bundle --model model.bin --config app.yaml --out-dir /tmp/pcr02-ai
rtk bash tools/debug/project-knowledge-debug.sh audit-binary --out /tmp/pcr02-binary-deps.txt --allow-missing
rtk bash tools/debug/project-knowledge-debug.sh crash-triage --core out/arm/app/core-xxxx --out-dir /tmp/pcr02-crash
rtk bash tools/debug/project-knowledge-debug.sh core-fastpass --core out/arm/app/core-xxxx
rtk bash tools/debug/project-knowledge-debug.sh core-match --core out/arm/app/core-xxxx
```

## 公共文档入口

- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/embedded-linux-performance-triage-guide.md`
- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/sigmastar-media-pipeline-triage-guide.md`
- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/yolo-ai-vision-deployment-guide.md`
- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/core-dump-capture-guide.md`
- `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/embedded-build-reproducibility-guide.md`
