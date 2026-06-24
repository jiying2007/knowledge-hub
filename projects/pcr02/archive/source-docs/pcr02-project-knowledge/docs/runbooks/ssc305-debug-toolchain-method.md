---
title: SSC305 调试工具链方法
doc_type: runbook
knowledge_type: process
maturity: draft
status: active
owner: team-core
created: 2026-05-28
last_updated: 2026-05-28
tags: [ssc305, debug, tools, crash, performance]
related: [../standards/ssc305-feishu-knowledge-map.md, embedded-linux-performance-triage-guide.md, core-dump-capture-guide.md, offline-gdb-core-fastpass-guide.md, asan-debug-guide.md, crash-bundle-collection-guide.md, sigmastar-media-pipeline-triage-guide.md]
validation_refs: [../../tools/debug/README.md, ../archive/sigmastar/manifest.csv]
---

# SSC305 调试工具链方法

## 1. 目标

本文定义 SSC305 项目调试时的工具选择、证据采集顺序和问题收口方式。核心原则是先采集可复现证据，再进入代码修改。

## 2. 工具分层

| 层级 | 工具或入口 | 目的 |
| --- | --- | --- |
| 环境确认 | `tools/debug/* env` 或项目 wrapper | 确认知识库、sysroot、目标程序、工具路径 |
| 运行基线 | `collect-runtime-baseline.sh` | 采集 CPU、内存、线程、fd、maps、进程状态 |
| 媒体快照 | `collect-media-pipeline-snapshot.sh` | 采集媒体链路运行证据 |
| crash bundle | `collect-crash-bundle.sh` | 收集 core、二进制、库、日志、maps |
| core 快速分析 | `gdb-core-fastpass.sh` | 快速获得 backtrace、线程、崩溃点 |
| core 深度分析 | `gdb-core-deeppass.sh` | 进一步分析局部变量、锁、内存布局 |
| 二进制匹配 | `verify-core-match.sh` | 确认 core 与可执行文件、so、sysroot 匹配 |
| ASAN | `asan-log-symbolize.sh` | 对 ASAN 日志离线符号化 |
| 依赖审计 | `audit-binary-deps.sh` | 检查二进制依赖是否完整 |

项目仓可以提供 wrapper 注入默认参数，但公共工具实现应维护在团队知识库 `tools/debug/`。

## 3. 调试前检查

先执行环境检查：

```bash
rtk bash tools/debug/project-knowledge-debug.sh env
```

若项目没有 wrapper，直接使用知识库公共脚本并显式传入参数：

```bash
rtk bash "$EMBEDDED_KNOWLEDGE_HOME/tools/debug/collect-runtime-baseline.sh" --proc <process_name> --duration 30 --out-dir /tmp/ssc305-runtime
```

必须确认：

1. 目标进程名正确。
2. 目标二进制与设备运行版本一致。
3. sysroot 与 core 所在设备固件一致。
4. 输出目录在 `/tmp`、受控 NAS 或问题单附件目录，不进入 Git。

## 4. 运行期异常采集顺序

适用于 CPU 高、内存涨、线程阻塞、fd 泄漏、延迟抖动、偶发卡死：

```bash
rtk bash tools/debug/project-knowledge-debug.sh runtime-baseline --duration 30 --out-dir /tmp/ssc305-runtime
```

采集后先判断：

1. CPU 是否集中在单线程。
2. RSS、PSS、heap、mmap 是否持续增长。
3. fd 是否增长，是否存在 socket、pipe、device 泄漏。
4. 线程数是否异常。
5. 日志时间戳是否与资源异常对齐。

## 5. crash 与 core 分析顺序

先收集完整 bundle：

```bash
rtk bash tools/debug/project-knowledge-debug.sh crash-triage --core <core_path> --out-dir /tmp/ssc305-crash
```

再做二进制匹配：

```bash
rtk bash tools/debug/project-knowledge-debug.sh core-match --core <core_path>
```

最后快速分析：

```bash
rtk bash tools/debug/project-knowledge-debug.sh core-fastpass --core <core_path>
```

结论必须包含：

1. 崩溃线程。
2. 信号类型。
3. 顶层 backtrace。
4. 二进制和 so 是否匹配。
5. 是否可定位到源码行。
6. 是否需要 deep pass 或复现验证。

## 6. ASAN 问题处理

ASAN 日志常见结论：

| 类型 | 判断方向 |
| --- | --- |
| heap-use-after-free | 生命周期、异步回调、队列持有对象 |
| heap-buffer-overflow | 数组边界、stride、payload 长度、协议解析 |
| stack-use-after-scope | 局部变量地址逃逸 |
| double-free | 错误所有权、失败路径重复释放 |
| leak | 退出路径、引用计数、长期任务对象 |

处理顺序：

1. 保存原始 ASAN 日志。
2. 用匹配的二进制和符号进行 symbolize。
3. 定位第一处有效错误，不从后续级联错误开始。
4. 写出对象所有权和释放路径。
5. 补最小复现或回归用例。

## 7. 证据命名

建议问题证据目录：

```text
/tmp/ssc305-<issue-id>/
  runtime/
  crash/
  media/
  logs/
  notes.md
```

`notes.md` 至少写：

```md
- issue_id:
- platform: SSC305
- firmware_version:
- process:
- trigger:
- collected_at:
- tool_commands:
- first_failure:
- owner:
```

## 8. 失败路径

1. 工具找不到：先检查 `EMBEDDED_KNOWLEDGE_HOME`，再检查公共脚本是否存在并可执行。
2. core 无法加载符号：先做二进制匹配，不要直接分析不匹配 backtrace。
3. 设备空间不足：只采最小证据，转存到受控路径后再继续。
4. 现场不能复现：保留 runtime baseline、日志时间窗和版本信息，禁止只写主观描述。

## 9. 收口标准

问题收口时至少给出：

1. 现象和触发条件。
2. 使用的工具命令。
3. 关键证据目录。
4. 根因层级：配置、资源、线程、内存、媒体链路、驱动、硬件或外部环境。
5. 修复或规避方案。
6. 回归命令和结果。
