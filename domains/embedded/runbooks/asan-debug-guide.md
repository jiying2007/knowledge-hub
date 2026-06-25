---
title: ASAN 调试指导（项目通用）
doc_type: runbook
knowledge_type: pitfall
maturity: verified
status: active
owner: team-core
created: 2026-05-12
last_updated: 2026-05-12
tags: [asan, memory, debug]
related: [asan-offline-symbolize-guide.md, crash-triage-checklist.md]
validation_refs: [tools/debug/asan-log-symbolize.sh, build/compile.mk]
---

# ASAN 调试指导（项目通用）

## 1. 目的

本文用于本项目的 AddressSanitizer（ASAN）调试，覆盖：

- 如何开启 ASAN 编译
- 如何验证 ASAN 是否生效
- 运行期建议参数
- 崩溃后的标准定位流程
- 项目内常见注意事项

离线地址符号化与快速归因，参考：

- [asan-offline-symbolize-guide.md](asan-offline-symbolize-guide.md)

---

## 2. 如何开启 ASAN（本项目）

### 2.1 开关规则

根据 `build/build.mk`：

- `DEBUG_ASAN=1` 的条件是：`DEBUG` 按位与 `256` 非 0，或按位与 `1` 非 0。
- 即常用值：`DEBUG=256` 或 `DEBUG=1`。

根据 `build/compile.mk`，开启后会自动追加：

- `-fsanitize=address`
- `-fno-omit-frame-pointer`
- `-fsanitize-recover=address`
- `-funwind-tables`

### 2.2 常用构建命令

全量构建（推荐）：

```bash
make -j8 DEBUG=256
```

构建并安装：

```bash
make -j8 DEBUG=256 && make install
```

仅编译某模块对象（示例）：

```bash
make modules/hdi_obj_all DEBUG=256 -j4
```

### 2.3 支持环境变量方式

除了命令行传参，也支持通过环境变量控制：

```bash
export DEBUG=256
make -j8
make install
```

临时环境变量写法：

```bash
DEBUG=256 make -j8
```

---

## 3. 如何确认 ASAN 已生效

### 3.1 看构建产物路径

开启 ASAN 后，构建系统会走 `debug` 相对目录逻辑（`TARGET_REL_FOLDER := debug`）。

### 3.2 看运行时依赖

在目标程序上检查是否依赖 `libasan`：

```bash
readelf -d /customer/bin/prog_pcr02 | rg -i asan
```

或在本地产物检查：

```bash
readelf -d release/bin/prog_pcr02 | rg -i asan
```

### 3.3 看启动日志

发生内存问题时，日志应出现：

- `AddressSanitizer: ...`
- `SUMMARY: AddressSanitizer: ...`

---

## 4. 运行期建议

### 4.1 建议环境变量

```bash
export ASAN_OPTIONS='abort_on_error=1:halt_on_error=1:detect_leaks=0:log_path=/tmp/asan:symbolize=1'
```

说明：

- `abort_on_error=1`：首个错误即中止，便于保留首发现场。
- `halt_on_error=1`：避免继续运行产生次生噪音。
- `detect_leaks=0`：嵌入式场景通常先聚焦崩溃/越界。
- `log_path`：把日志落盘，避免串口丢失。
- `symbolize=1`：开启 ASAN 自带符号化流程（前提是符号与工具链可用）。

### 4.2 可选符号化器

如需更稳定的符号化，可显式指定：

```bash
export ASAN_SYMBOLIZER_PATH=/usr/bin/llvm-symbolizer
```

若环境没有 `llvm-symbolizer`，不影响 ASAN 检测本身，但可读栈信息会变差。

---

## 5. 标准定位流程

### Step 1：只看首发错误

优先抓第一条 ASAN 报错，不要先看后续连锁日志。

### Step 2：确认二进制与符号匹配

检查 BuildID：

```bash
readelf -n /customer/bin/prog_pcr02 | rg -i build.id
readelf -n release/bin/prog_pcr02 | rg -i build.id
```

BuildID 必须一致。

### Step 3：从 ASAN 栈直接提取定位信息

优先使用 ASAN 报告内自带的函数名和源码行号（`#0/#1/...` 栈帧）。

若没有行号，先确认：

- 是否使用 ASAN 构建
- 是否带调试符号
- `ASAN_OPTIONS` 中是否开启 `symbolize=1`
- 是否设置了 `ASAN_SYMBOLIZER_PATH`

### Step 4：建立最小调用链

至少保留：

- 崩溃函数 + 行号
- 直接调用者
- 模块入口
- 进程入口

### Step 5：最小修复并复现

- 先修必崩点
- 控制改动范围
- 复现同一路径验证是否消失

---

## 6. 项目内注意事项

1. 开启 ASAN 后不要混用旧的 release 包进行符号化。
2. 构建脚本在 `DEBUG_ASAN=1` 时会避免对可执行和库做 strip，有助于回溯。
3. 考虑固件分区容量，`libs/3rdparty/libasan` 默认不预置到固件镜像；使用 ASAN 时需手动将 `libasan` 拷贝到目标机 `/customer/lib`。
4. 建议同时拷贝版本文件和符号链接，避免动态链接器找不到 `libasan.so.6`。
5. `-fsanitize-recover=address` 已开启，若希望首错即停，务必配 `ASAN_OPTIONS=abort_on_error=1`。
6. 线程多、日志量大时，优先落盘日志（`log_path`），避免串口截断。

---

## 7. 常用命令速查

开启 ASAN 全量构建：

```bash
make -j8 DEBUG=256
```

安装：

```bash
make install
```

环境变量方式：

```bash
export DEBUG=256
make -j8
```

检查 ASAN 依赖：

```bash
readelf -d /customer/bin/prog_pcr02 | rg -i asan
```

部署 `libasan` 到目标机（示例）：

```bash
cp -av libs/3rdparty/libasan/libasan.so* /customer/lib/
```

建议运行参数：

```bash
export ASAN_OPTIONS='abort_on_error=1:halt_on_error=1:detect_leaks=0:log_path=/tmp/asan:symbolize=1'
```
