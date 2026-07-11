---
title: PCR02 SSC305 第三方库编译优化基线
doc_type: runbook
knowledge_type: build
maturity: verified
status: active
owner: team-core
created: 2026-07-10
last_updated: 2026-07-10
tags: [pcr02, ssc305, thirdparty, build, optimization, cortex-a7, neon, hard-float, libyuv]
related: [project-build-and-deploy-guide.md, project-debug-tools-guide.md]
validation_refs:
  - sigdoc/customer/DualOS/EnvironmentSetup/Environmentsetup_zh.html
  - sigdoc/customer/Common/Development/alkaid_defconfig_zh.html
  - workspace://xcrz-sigmastar-demo/3rdparty/build/build_sh/common/env.sh
  - workspace://xcrz-sigmastar-demo/build/compile.mk
---

# PCR02 SSC305 第三方库编译优化基线

## 1. 适用范围

本 runbook 适用于 PCR02 / SigmaStar SSC305 上的第三方库移植与性能优化，特别是 `3rdparty` 下通过项目构建规则接入的图像、音频、算法和通用 C/C++ 库。

后续新增或重构第三方库时，默认先参考本基线，再按库自身风险做局部覆盖。不要把激进优化选项无验证地扩散到全工程。

## 2. 平台事实

SigmaStar 文档确认 Linux / Alkaid / Kernel 侧使用 glibc 交叉工具链：

```text
gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf
```

对应交叉编译前缀：

```text
arm-linux-gnueabihf-
```

文档也说明 toolchain 属于 bringup 前确定的基础配置，影响 release 安装路径和工具链命名，不应在普通第三方库移植中随意切换。

对该工具链的本地实测结论：

```text
-march=armv7-a+neon-vfpv4
-mfloat-abi=hard
-mfpu=neon-vfpv4
```

预定义宏确认：

```text
__ARM_ARCH 7
__ARM_ARCH_7A__ 1
__ARM_NEON 1
__ARM_NEON__ 1
__ARM_PCS_VFP 1
```

因此，PCR02 SSC305 glibc Linux 侧默认已经是 ARMv7-A、NEON/VFPv4、hard-float ABI。第三方库不应切换到 `softfp` 或其它 ABI，否则会与现有系统库和预编译库产生 ABI 风险。

## 3. 推荐分层

### 3.1 保守基线

当前 `3rdparty` 构建环境默认偏体积优化：

```text
-Os -ffunction-sections -fdata-sections -fPIC
```

适用场景：

- 非热点库。
- 体积优先库。
- 移植初期先求 ABI 和功能稳定。
- 没有板端性能基准数据的库。

### 3.2 性能候选

对 `libyuv`、像素转换、音视频处理、算法热路径等第三方库，优先试用：

```text
-O3 -DNDEBUG -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -ffunction-sections -fdata-sections -fPIC
```

C++ 库的 `CXXFLAGS` 可使用同等组合。

选项含义：

- `-O3`：适合热点计算库，可触发更积极的内联、循环优化和向量化。
- `-DNDEBUG`：发布库应去掉 assert，减少运行时开销。
- `-mcpu=cortex-a7`：工具链实测支持，可让 GCC 按 Cortex-A7 做指令选择和调度。
- `-mfpu=neon-vfpv4`：显式固定 NEON/VFPv4，与平台默认一致。
- `-mfloat-abi=hard`：显式固定 hard-float ABI，与 glibc 工具链和现有库一致。
- `-ffunction-sections -fdata-sections`：配合链接 `--gc-sections` 裁剪未用代码。
- `-fPIC`：第三方共享库和可复用对象默认保留。

### 3.3 发布实验项

以下选项只能作为专项实验，必须有板端性能数据、功能回归和一致性测试后再固化：

```text
-flto
-marm
-funroll-loops
```

说明：

- `-flto` 可做链接时跨文件优化，但会增加构建时间，并可能影响符号、调试和第三方库链接流程。
- 当前工具链默认 `-mthumb`，项目构建中也有 Thumb 使用痕迹；热点循环可局部测试 `-marm`，不能默认全局切换。
- `-funroll-loops` 可能提高个别循环性能，也可能增大代码体积和 I-cache 压力。

## 4. 谨慎或默认禁用项

不要在第三方库移植第一阶段默认打开：

```text
-Ofast
-ffast-math
-fopenmp
```

原因：

- `-Ofast` 和 `-ffast-math` 会放宽 C/C++ 与 IEEE 浮点语义。对音频、图像、算法库可能引入精度或一致性差异，只能在明确验证后局部启用。
- `-fopenmp` 需要确认 `libgomp`、rootfs、调度和线程模型。小颗粒图像处理可能被线程调度、缓存争用或内存带宽抵消收益。

## 5. libyuv 当前结论

已构建的 `libyuv.so` 通过 `readelf -A` 检查，属性包含：

```text
Tag_CPU_arch: v7
Tag_FP_arch: VFPv4
Tag_Advanced_SIMD_arch: NEONv1 with Fused-MAC
Tag_ABI_VFP_args: VFP registers
```

这说明现有产物已经是 ARMv7 + VFPv4 + NEON + hard-float ABI。

后续如要进一步压榨 libyuv 性能，优先在库级别试用性能候选组合：

```text
-O3 -DNDEBUG -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -ffunction-sections -fdata-sections -fPIC
```

不要先把 `-Ofast`、`-ffast-math` 或 `-flto` 作为默认项。

## 6. 临时验证命令

在 `3rdparty` 目录下，可以用环境变量临时覆盖第三方库构建参数：

```bash
rtk bash -lc 'export THIRDPARTY_CROSS_PREFIX=/tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf; export THIRDPARTY_C_FLAGS="-O3 -DNDEBUG -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -ffunction-sections -fdata-sections -fPIC"; export THIRDPARTY_CXX_FLAGS="-O3 -DNDEBUG -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -ffunction-sections -fdata-sections -fPIC"; bash build/build.sh build libyuv'
```

构建后检查 ABI 和 SIMD 属性：

```bash
rtk /tools/toolchain/gcc-11.1.0-20210608-sigmastar-glibc-x86_64_arm-linux-gnueabihf/bin/arm-linux-gnueabihf-readelf -A libs/3rdparty/libyuv/lib/libyuv.so
```

重点确认：

```text
Tag_FP_arch
Tag_Advanced_SIMD_arch
Tag_ABI_VFP_args
Tag_CPU_name
```

## 7. 固化规则

新增第三方库时按以下顺序处理：

1. 先用保守基线完成移植，确认 ABI、链接和功能。
2. 对热点库单独启用性能候选组合。
3. 板端跑最小性能基准和功能回归。
4. 用 `readelf -A` 确认 hard-float、NEON/VFP 属性。
5. 若需要 `-flto`、`-marm`、`-Ofast`、`-ffast-math` 或 `-fopenmp`，必须单独记录验证证据。

不要因为一个库验证通过，就把激进选项扩散到所有第三方库或主工程。

## 8. 归档证据

- Source: 当前 Codex 会话对 SSC305 sigdoc、工程 build 规则、GCC target help、预定义宏和 libyuv 产物属性的只读分析。
- Topic: `pcr02-ssc305-thirdparty-build-optimization-baseline`
- Captured at: 2026-07-10
- Last verified: 2026-07-10
- Sanitization: 未包含 secrets、token、raw log、core、SDK 包或二进制内容。
- Provenance: SigmaStar 本地文档、PCR02 `3rdparty` 构建规则、平台 GCC 11.1 工具链实测。
- Verification: 工具链 target 查询、宏查询、`-O3 -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard` smoke 编译、`readelf -A` 检查既有 libyuv 产物。
- Memory Candidate: no。项目级 current runbook 已作为后续第三方库参考入口。
- Gate Result: pass。
