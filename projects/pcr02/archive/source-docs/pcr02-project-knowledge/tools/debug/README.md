# debug tools

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

## 快速使用

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

rtk sh tools/debug/busybox-kernel-io-watch.sh --proc "$PROJECT_EXE" --interval 1 --top 10
rtk sh tools/debug/busybox-kernel-io-watch.sh --pid 913 --duration 120 --out /tmp/io-watch.log
rtk sh tools/debug/busybox-kernel-io-watch.sh --proc "$PROJECT_EXE" --duration 180 --snapshot 1 --snapshot-dir /tmp/io-watch-snapshots --snapshot-cooldown 15 --snapshot-max 30
rtk sh tools/debug/busybox-kernel-io-watch.sh --proc "$PROJECT_EXE" --duration 180 --pack 1 --pack-dir /tmp --pack-prefix io-watch

# 如果已拷回设备动态库，可显著提升符号化质量
rtk bash tools/debug/gdb-core-fastpass.sh --bin "$PROJECT_APP_DIR/$PROJECT_EXE.debug.full" --core "$PROJECT_APP_DIR/core-xxxx" --sysroot out/arm/target --solib-search-path out/arm/target/customer/lib:out/arm/target/lib:out/arm/target/usr/lib
```
