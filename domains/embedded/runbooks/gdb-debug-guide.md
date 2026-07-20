---
title: GDB 调试指导（项目通用）
doc_type: runbook
knowledge_type: process
maturity: verified
status: archived
searchable: false
owner: team-core
created: 2026-05-14
last_updated: 2026-05-14
tags: [gdb, debug, crash]
related: [asan-debug-guide.md, core-binary-match-verification-guide.md, crash-bundle-collection-guide.md]
validation_refs: [build/build.mk, build/compile.mk]
---

# GDB 调试指导（项目通用）

## 1. 目的

本文用于本项目 Linux 用户态程序（`prog_pcr02/prog_daemon/prog_cmd_server` 等）调试，覆盖：

1. glibc 工具链下的统一调试环境
2. 可部署瘦身二进制与符号分离
3. 目标板 `gdbserver` 启动（含缺库场景）
4. 主机连接与常用定位动作
5. core 离线分析与常见报错处理

---

## 配套工具（新增）

若希望减少重复输入并控制输出长度，优先配合以下脚本：

1. `tools/debug/gdb-core-fastpass.sh`：低输出首轮定位
2. `tools/debug/gdb-core-deeppass.sh`：二轮增强定位
3. `tools/debug/core-env-snapshot.sh`：环境与证据快照
4. `tools/debug/verify-core-match.sh`：core 与 binary 配对校验
5. `tools/debug/collect-crash-bundle.sh`：崩溃材料一键打包
6. `tools/debug/match-build-artifact.sh`：按 core 反查最可能符号文件
7. `tools/debug/summarize-gdb-fastpass.sh`：fastpass 输出摘要化
8. `tools/debug/extract-crash-signature.sh`：崩溃签名提取

对应流程说明见：

1. [core-dump-capture-guide.md](core-dump-capture-guide.md)
2. [offline-gdb-core-fastpass-guide.md](offline-gdb-core-fastpass-guide.md)
3. [crash-triage-checklist.md](crash-triage-checklist.md)
4. [core-binary-match-verification-guide.md](core-binary-match-verification-guide.md)
5. [crash-bundle-collection-guide.md](crash-bundle-collection-guide.md)

---

## 2. 适用范围与术语

适用范围：

1. 本仓库用户态进程（如 `prog_pcr02`、`prog_daemon`、`prog_cmd_server`）。
2. 主机与目标板均按本手册固定 glibc 工具链路径执行。
3. 问题类型包括崩溃、卡死、异常返回、线程竞争、疑似野指针。

关键术语：

1. 未 strip 二进制：包含完整符号表，便于断点和源码行号定位。
2. strip 二进制：体积小，但调试信息可能被移除。
3. BuildID：用于确认“运行程序”和“符号文件”是否同源构建。
4. `gdbserver`：运行在目标机，负责与主机 GDB 建立远程调试通道。

---

## 3. 调试前置检查清单

1. 已完成项目构建，产物可执行（具体构建流程以项目仓手册为准）。
2. 主机只使用平台工具链 GDB：`/tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-gdb`。
3. 目标板 `gdbserver` 只使用 glibc 工具链版本。
4. 必须保证“运行二进制”与“符号文件”来自同一次构建。

建议固定变量（主机）：

```bash
export PLATFORM_GDB=/tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-gdb
export PLATFORM_TC=/tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf
export TARGET_GDBSERVER=$PLATFORM_TC/arm-linux-gnueabihf/usr/bin/gdbserver
export TARGET_SYSROOT=$PLATFORM_TC/arm-linux-gnueabihf
```

工具组合策略（本项目推荐）：

1. 业务编译/链接使用 glibc 工具链（`arm-linux-gnueabihf-*`）。
2. 主机调试器使用 glibc 工具链 GDB（`$PLATFORM_GDB`）。
3. 目标板调试代理必须使用 glibc 工具链 `gdbserver`（`$TARGET_GDBSERVER`）。
4. 若板端缺少 glibc 依赖库，使用“携带运行时库 + 显式 loader”方式启动（见 6.1）。
5. 禁止混用 glibc 与 uclibc 业务库做链接。

主机侧检查（在仓库根目录）：

```bash
rtk bash -lc "test -x /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-gdb && echo OK || echo MISSING"
rtk bash -lc "test -x /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf/usr/bin/gdbserver && echo OK || echo MISSING"
rtk bash -lc "ls -l out/arm/app/prog_pcr02"
```

目标机检查（在目标机 shell，不走 `rtk`）：

```bash
ping -c 3 <HOST_IP>
ls -l /customer/bin/prog_pcr02
df -h /customer /tmp /mnt
```

---

## 4. 生成可调试产物

### 4.1 编译阶段说明

1. 本项目默认编译参数包含 `-g`（见 `build/compile.mk`），会生成调试信息。
2. 非 ASAN 场景下，`make install` 对部分产物会 strip，板端符号可能不完整。
3. ASAN 场景通常符号更完整，但产物更大，运行开销更高。

### 4.2 推荐做法（调试友好）

1. 主机完整构建：

```bash
rtk make -j8 all
```

2. 保留主机侧未 strip 二进制（通常在 `out/<arch>/app/`）。
3. 上板后允许运行 strip 二进制，但主机 GDB 必须加载未 strip 对应文件。

### 4.3 符号分离（推荐长期使用）

目标：板端二进制小，主机仍保留完整符号。

在主机执行（固定 glibc 工具链）：

```bash
rtk bash -lc "cp out/arm/app/prog_pcr02 out/arm/app/prog_pcr02.debug.full"
rtk bash -lc "$PLATFORM_TC/bin/arm-linux-gnueabihf-objcopy --only-keep-debug out/arm/app/prog_pcr02 out/arm/app/prog_pcr02.debug"
rtk bash -lc "$PLATFORM_TC/bin/arm-linux-gnueabihf-strip --strip-unneeded out/arm/app/prog_pcr02"
rtk bash -lc "$PLATFORM_TC/bin/arm-linux-gnueabihf-objcopy --add-gnu-debuglink=out/arm/app/prog_pcr02.debug out/arm/app/prog_pcr02"
rtk bash -lc "ls -lh out/arm/app/prog_pcr02 out/arm/app/prog_pcr02.debug out/arm/app/prog_pcr02.debug.full"
```

说明：

1. `prog_pcr02` 为瘦身后的可部署版本。
2. `prog_pcr02.debug` 与 `prog_pcr02.debug.full` 保留在主机，不能丢。
3. 若未配置 `debuglink` 自动加载，可在 GDB 手工 `symbol-file out/arm/app/prog_pcr02.debug`。

### 4.4 生成可部署瘦身版并上板（解决分区空间不足）

适用场景：`/customer` 分区空间不足，原始 `prog_pcr02` 无法直接拷贝。

1. 主机生成瘦身版（见 4.3）。
2. 将瘦身版拷贝到目标板可用分区（推荐 `/mnt`）：

```bash
scp out/arm/app/prog_pcr02 root@<TARGET_IP>:/mnt/prog_pcr02
```

3. 若业务脚本要求固定路径 `/customer/bin/prog_pcr02`，用软链接接入：

```bash
ssh root@<TARGET_IP> "rm -f /customer/bin/prog_pcr02 && ln -s /mnt/prog_pcr02 /customer/bin/prog_pcr02 && ls -l /customer/bin/prog_pcr02"
```

4. 调试时主机侧仍加载同版本符号文件：

```gdb
file out/arm/app/prog_pcr02
symbol-file out/arm/app/prog_pcr02.debug
```

5. 上板后必须再次校验 BuildID 一致（见第 5 章），防止“可执行文件与符号不匹配”。

---

## 5. 版本一致性校验（强烈建议）

在主机与目标机分别校验 BuildID，必须一致：

主机（仓库根目录）：

```bash
rtk bash -lc "readelf -n out/arm/app/prog_pcr02 | rg -i 'Build ID|build.id'"
```

目标机：

```bash
readelf -n /mnt/prog_pcr02 | grep -i -E "Build ID|build.id"
# 或 readelf -n /customer/bin/prog_pcr02 | grep -i -E "Build ID|build.id"（若走软链接/直拷）
```

不一致时，不要继续调试，先重新部署对应版本。

---

## 6. 远程调试（推荐主路径）

以下以 `prog_pcr02` 为例，其他进程同理。

### 6.1 目标机启动 `gdbserver`

使用 glibc 工具链 `gdbserver`（本项目要求）：

```bash
scp "$TARGET_GDBSERVER" root@<TARGET_IP>:/tmp/gdbserver
ssh root@<TARGET_IP> "chmod +x /tmp/gdbserver && /tmp/gdbserver --version"
```

若板端直接执行失败（常见报缺库），使用显式 loader 启动：

```bash
ssh root@<TARGET_IP> "mkdir -p /tmp/glibc-gdb/lib /tmp/glibc-gdb/usr/lib"
scp /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf/lib/ld-linux-armhf.so.3 root@<TARGET_IP>:/tmp/glibc-gdb/lib/
scp /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf/lib/libc.so.6 root@<TARGET_IP>:/tmp/glibc-gdb/lib/
scp /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf/lib/libpthread.so.0 root@<TARGET_IP>:/tmp/glibc-gdb/lib/
scp /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf/lib/libm.so.6 root@<TARGET_IP>:/tmp/glibc-gdb/lib/
scp /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf/lib/libdl.so.2 root@<TARGET_IP>:/tmp/glibc-gdb/lib/
scp /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf/lib/libgcc_s.so.1 root@<TARGET_IP>:/tmp/glibc-gdb/lib/
scp /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf/usr/lib/libstdc++.so.6 root@<TARGET_IP>:/tmp/glibc-gdb/usr/lib/
```

方式 A：启动新进程并等待连接

```bash
/tmp/gdbserver :2345 /customer/bin/prog_pcr02
# 若程序实际放在 /mnt：/tmp/gdbserver :2345 /mnt/prog_pcr02
```

方式 B：附加到已运行进程（推荐排查线上现象）

```bash
pidof prog_pcr02
/tmp/gdbserver :2345 --attach <PID>
```

方式 C：显式 loader + attach（缺库场景）

```bash
/tmp/glibc-gdb/lib/ld-linux-armhf.so.3 --library-path /tmp/glibc-gdb/lib:/tmp/glibc-gdb/usr/lib /tmp/gdbserver :2345 --attach <PID>
```

连通性检查（主机）：

```bash
ping -c 3 <TARGET_IP>
nc -vz <TARGET_IP> 2345
```

### 6.2 主机连接

```bash
$PLATFORM_GDB out/arm/app/prog_pcr02
```

进入 GDB 后，建议先做基础配置：

```gdb
set pagination off
set confirm off
set print pretty on
set print object on
set breakpoint pending on
set disassemble-next-line on
set sysroot /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/arm-linux-gnueabihf
set auto-solib-add off
set solib-search-path /customer/lib
symbol-file out/arm/app/prog_pcr02.debug
target remote 172.16.16.27:2345
sharedlibrary
```

若源码路径不一致，补充路径映射：

```gdb
directory /path/to/project
set substitute-path /build_agent/workspace /path/to/project
```

---

## 7. 常见调试动作（按场景）

### 7.1 断点与执行控制

```gdb
break main
break modules/sensor/display/display_control.cpp:120
break display::DisplayControl::UpdateFrame
tbreak main
continue
next
step
finish
until 200
```

### 7.2 线程问题定位

```gdb
info threads
thread 3
bt
thread apply all bt full
```

建议：

1. 先执行 `thread apply all bt full` 保存全线程现场。
2. 再逐线程切换，优先检查持锁线程和异常线程。

### 7.3 变量、指针、寄存器检查

```gdb
info locals
info args
print variable_name
print *ptr
x/16wx ptr
ptype variable_name
info registers
```

### 7.4 观察点（定位谁改坏了变量）

```gdb
watch variable_name
rwatch variable_name
awatch variable_name
continue
```

### 7.5 信号与异常控制

```gdb
handle SIGPIPE nostop noprint pass
handle SIGSEGV stop print pass
catch throw
catch syscall
```

---

## 8. 多进程与守护进程场景

### 8.1 程序会 fork 子进程

```gdb
set follow-fork-mode child
set detach-on-fork off
```

### 8.2 只想调某个已运行子进程

1. 在目标机先 `pidof <name>` 找 PID。
2. `/tmp/gdbserver :2345 --attach <PID>`。
3. 主机 `target remote` 接入后先 `thread apply all bt` 抓现场。

---

## 9. Core 文件离线调试（推荐备选路径）

### 9.1 目标机开启 core dump

```bash
ulimit -c unlimited
echo /tmp/core.%e.%p > /proc/sys/kernel/core_pattern
```

### 9.2 采集文件清单

至少保留：

1. core 文件（例如 `/tmp/core.prog_pcr02.1234`）
2. 崩溃时可执行文件
3. 依赖库目录（最少 `/customer/lib` 里相关 `.so`）
4. 对应源码版本标识（commit 或 BuildID）

### 9.3 主机离线分析

```bash
$PLATFORM_GDB out/arm/app/prog_pcr02 /path/to/core.prog_pcr02.1234
```

进入后优先执行：

```gdb
set pagination off
info files
thread apply all bt full
frame 0
info locals
info registers
x/i $pc
```

---

## 10. 常见报错与处理

1. `No symbol table is loaded`
原因：GDB 加载的是 strip 后程序。
处理：改用未 strip 文件执行 `file <path>`；若使用符号分离流程，再执行 `symbol-file out/arm/app/prog_pcr02.debug`。

2. `Remote communication error` 或连接超时
原因：网络不可达、端口被占用、`gdbserver` 未启动。
处理：目标机确认 `gdbserver` 进程和端口；主机确认 IP/端口连通。

3. 断点显示 `pending` 一直不命中
原因：符号尚未加载或函数未执行到。
处理：启用 `set breakpoint pending on`；确认符号文件一致；检查断点函数是否被调用。

4. 行号错乱或跳转异常
原因：二进制和源码不一致，或优化导致映射复杂。
处理：先核对 BuildID；必要时以同版本源码重建后再调。

5. 动态库里断点不生效
原因：GDB 未找到动态库符号。
处理：设置 `set solib-search-path` 和 `set sysroot`，并保证 `.so` 版本一致。

6. `gdbserver` 启动时报 `No such file or directory`
原因：常见是动态加载器或 glibc 依赖库缺失，不是文件路径不存在。
处理：按 6.1 使用“显式 loader + library-path”方式启动。

7. `target remote` 后读取 `ld-linux-armhf.so.3` 断开
原因：远端 `gdbserver`/依赖库不稳定或传输远端 so 失败。
处理：先 `set sysroot` 指向本地工具链 sysroot，再连接；必要时 `set auto-solib-add off` 后重连，并查看板端 `gdbserver` 日志。

---

## 11. 推荐 `.gdbinit` 模板

可在项目内保存 `docs/runbooks/examples/gdbinit-pcr02`，连接前执行 `source`：

```gdb
set pagination off
set confirm off
set print pretty on
set print object on
set breakpoint pending on
set disassemble-next-line on
set auto-solib-add off
handle SIGPIPE nostop noprint pass
define btall
  thread apply all bt full
end
document btall
  Print full backtrace for all threads.
end
```

使用方式：

```gdb
source docs/runbooks/examples/gdbinit-pcr02
target remote <TARGET_IP>:2345
```

---

## 12. 与 ASAN 的协同建议

1. 内存越界/Use-After-Free：先 ASAN 抓首发，再 GDB 深挖上下文。
2. 时序/死锁/竞争：优先 GDB，多线程栈和锁等待更直观。
3. 量产接近性验证：优先非 ASAN + GDB；问题难复现再切 ASAN。

参考：[asan-debug-guide.md](asan-debug-guide.md)

---

## 13. 最小实战流程（10 分钟版）

1. 主机构建：`rtk make -j8 all`
2. 符号分离：按 4.3 生成 `prog_pcr02.debug` 与瘦身版 `prog_pcr02`
3. 上板部署：按 4.4 拷贝到 `/mnt`，必要时软链接到 `/customer/bin/prog_pcr02`
4. 目标机起服务：`/tmp/gdbserver :2345 /customer/bin/prog_pcr02`（或 `/mnt/prog_pcr02`）
5. 主机连接：`$PLATFORM_GDB out/arm/app/prog_pcr02`
6. GDB 设置：`set sysroot ...`、`symbol-file out/arm/app/prog_pcr02.debug`、`target remote <TARGET_IP>:2345`
7. 抓首现场：`thread apply all bt full`
8. 进入关键帧：`frame <n>` + `info locals` + `print`
9. 记录结论：崩溃线程、首发函数、可复现路径、修复假设
