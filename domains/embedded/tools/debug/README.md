# debug tools

**运行身份与安全门槛：** 本页仅保存 Hub 侧候选工具使用说明。所有 `tools/debug/` 相对脚本路径以 `workspace://embedded-knowledge` 团队仓的实际 checkout 根目录为执行 cwd，必须先核真实文件、源码提交和权限。设备 core、日志、序列号、网络地址、客户信息只在批准的私有证据位置采集；不能复制完整原始材料到公开 Hub。 

**危害性操作：** NAND 写入压测、OTA 升级、格式化、擦写和改变内核日志ring buffer只适用于经授权的隔离测试设备，必须有恢复/备份、存储预算和明确责任人；本页不提供可直接执行的复合压测/OTA命令。默认采集仍以非清空 `--dmesg-mode snapshot` 为准。

## 文件说明

1. `gdb-core-fastpass.sh`
- 低输出核心分析脚本，适合第一轮定位。

2. `gdb-core-deeppass.sh`
- 增强输出核心分析脚本，适合疑难问题二次定位。

3. `core-env-snapshot.sh`
- 导出主机侧 core 调试环境快照，便于问题单附证据。

4. `verify-core-match.sh`
- 检查 core 与 binary/debug.full 是否可配对离线分析。
- 默认输出低噪音摘要，完整 gdb 输出落盘，适合低 token 调试。

5. `collect-crash-bundle.sh`
- 一键打包 core、符号文件、环境快照与附加材料。

6. `triage-crash-bundle.sh`
- 串联 core 匹配、二进制依赖审计、gdb fastpass 和 signature 提取。

7. `asan-log-symbolize.sh`
- 将 ASAN 日志地址批量离线符号化到函数/行号。

8. `summarize-gdb-fastpass.sh`
- 从 fastpass/deeppass 输出自动提炼低 token 摘要。

9. `extract-crash-signature.sh`
- 从 gdb 输出提取稳定崩溃签名，便于聚类与去重。

10. `match-build-artifact.sh`
- 从 core 文件自动匹配最可能的 `*.debug.full`。
- 优先读取 core 内 `execfn` 做匹配，避免线程名导致误配。

11. `busybox-kernel-io-watch.sh`
- 面向 SSC305 BusyBox 的在线排障脚本：关联 `dmesg` 内核异常与线程级 I/O 增量。
- 支持命中关键字自动抓快照和打包。

12. `collect-runtime-baseline.sh`
- 采集运行期性能第一现场：`top/ps/free/df/dmesg/proc/fd/thread/wchan`。

13. `collect-media-pipeline-snapshot.sh`
- 采集媒体链路第一现场：进程、线程、fd、dmesg、media device、相关模块。

14. `collect-ai-vision-bundle.sh`
- 采集 AI Vision 证据包：模型/config metadata、进程状态、AI 设备节点和 runtime 日志线索。

15. `audit-binary-deps.sh`
- 审计 ELF 架构、build-id、NEEDED 动态库和 sysroot 中依赖是否存在。

16. `busybox-nand-io-pressure.sh`
- BusyBox 环境下的 SPI NAND/UBIFS I/O 压力脚本。
- 提供并发写入、读回校验、元数据突发创建删除和可选周期性 `sync`。

17. `busybox-nand-stress-suite.sh`
- 压测编排脚本：并行启动 `busybox-kernel-io-watch.sh` 与 `busybox-nand-io-pressure.sh`。
- 自动收集 `watch.log`、`pressure.log`、`summary.txt` 和前后 `dmesg` 快照。

## 快速使用

### 1) Core/崩溃调试

```bash
export PROJECT_APP_DIR="${PROJECT_APP_DIR:-out/arm/app}"
export PROJECT_EXE="${PROJECT_EXE:-prog_pcr02}"

rtk bash tools/debug/gdb-core-fastpass.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --core "$PROJECT_APP_DIR/core-xxxx"
rtk bash tools/debug/gdb-core-deeppass.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --core "$PROJECT_APP_DIR/core-xxxx"
rtk bash tools/debug/core-env-snapshot.sh --output "$PROJECT_APP_DIR/core-env"
rtk bash tools/debug/verify-core-match.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --core "$PROJECT_APP_DIR/core-xxxx"
rtk bash tools/debug/collect-crash-bundle.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --core "$PROJECT_APP_DIR/core-xxxx"
rtk bash tools/debug/triage-crash-bundle.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --core "$PROJECT_APP_DIR/core-xxxx" --out-dir "$PROJECT_APP_DIR/crash-triage"
rtk bash tools/debug/asan-log-symbolize.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --log "$PROJECT_APP_DIR/asan.log"
rtk bash tools/debug/summarize-gdb-fastpass.sh --in "$PROJECT_APP_DIR/gdb-fastpass/fastpass-xxxx.txt"
rtk bash tools/debug/extract-crash-signature.sh --in "$PROJECT_APP_DIR/gdb-fastpass/fastpass-xxxx.txt"
rtk bash tools/debug/match-build-artifact.sh --core "$PROJECT_APP_DIR/core-xxxx"
rtk bash tools/debug/audit-binary-deps.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --sysroot out/arm/target --out "$PROJECT_APP_DIR/binary-deps.txt" --allow-missing
rtk bash tools/debug/collect-runtime-baseline.sh --proc "$PROJECT_EXE" --duration 30 --out-dir /tmp/runtime-baseline
rtk bash tools/debug/collect-media-pipeline-snapshot.sh --proc "$PROJECT_EXE" --out-dir /tmp/media-pipeline
rtk bash tools/debug/collect-ai-vision-bundle.sh --proc "$PROJECT_EXE" --model model.bin --config app.yaml --out-dir /tmp/ai-vision
```

### 2) BusyBox 内核 I/O 监控

默认推荐（不清空 ring buffer，日志只落文件）：

```bash
rtk sh tools/debug/busybox-kernel-io-watch.sh --proc "$PROJECT_EXE" --duration 180 --dmesg-mode snapshot --out /tmp/io-watch.log --stdout 0
```

复现场景抓快照（命中关键字时自动抓取并打包）：

```bash
rtk sh tools/debug/busybox-kernel-io-watch.sh --proc "$PROJECT_EXE" --duration 180 --dmesg-mode snapshot --snapshot 1 --snapshot-dir /tmp/io-watch-snapshots --snapshot-cooldown 15 --snapshot-max 30 --out /tmp/io-watch.log --stdout 0
```

兼容场景（已知 PID，短时定位）：

```bash
rtk sh tools/debug/busybox-kernel-io-watch.sh --pid 913 --duration 120 --out /tmp/io-watch.log
```

参数边界：
- 默认不建议 `--dmesg-mode clear`，除非你明确要“只看新日志且允许清空 ring buffer”。
- `--idle-log-every` 仅用于进一步降噪，建议在默认命令上追加，不单独作为主示例。

### 3) SPI NAND 压测（受控实验，不是默认命令）

高负载NAND写入与OTA同时运行可能影响设备分区、数据和现场日志，不能从Hub复制一次历史命令直接运行。进入实验前先在团队仓实际源码检查 `busybox-nand-io-pressure.sh` 与 `busybox-nand-stress-suite.sh` 的当前参数、路径与负向门禁，由设备责任人指定隔离介质及备份/恢复流程，并执行受限预算的独立试验。

**没有已授权的专用实验目录、设备身份、固件基线、数据备份和恢复方式时，保持 `not-run`。** 历史 `/data/io-stress` 与联动 `/data/app_ota/ota_upgrade.sh` 仅为旧环境线索，不是本文提供的可执行调用。独立保存真实执行退出码、dmesg快照和可复核结果；不要把测试计划写成PASS。

如果已拷回设备动态库，可显著提升符号化质量：

```bash
rtk bash tools/debug/gdb-core-fastpass.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --core "$PROJECT_APP_DIR/core-xxxx" --sysroot out/arm/target --solib-search-path out/arm/target/customer/lib:out/arm/target/lib:out/arm/target/usr/lib
```
