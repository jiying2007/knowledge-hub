---
title: SSC305 构建烧录升级方法
doc_type: runbook
knowledge_type: process
maturity: draft
status: active
owner: team-core
created: 2026-05-28
last_updated: 2026-05-28
tags: [ssc305, build, burn, ota, delivery]
related: [../standards/ssc305-feishu-knowledge-map.md, sigmastar-platform-development-workflow.md, embedded-build-reproducibility-guide.md, sigmastar-sdk-upgrade-playbook.md]
validation_refs: [../archive/sigmastar/manifest.csv, ../../tools/debug/README.md]
---

# SSC305 构建烧录升级方法

## 1. 适用范围

本文用于建立 SSC305 项目从源码构建到设备运行、烧录、升级和回滚的通用方法。具体命令以项目仓 `Makefile`、产品配置和发布脚本为准。

适用任务：

1. 新环境首次构建。
2. SDK 或产品配置变更后重建。
3. 生成 release 目录、升级包或烧录包。
4. 设备启动失败、升级失败、分区异常的初步定位。

## 2. 前置检查

| 检查项 | 方法 |
| --- | --- |
| 工具链 | 确认 `TOOLCHAIN`、`TOOLCHAIN_VERSION`、交叉编译器路径存在 |
| 项目变量 | 确认 `PROJ_ROOT`、`CHIP`、`PRODUCT` 等变量与目标板一致 |
| 依赖库 | 确认第三方库、预编译库、SDK lib 路径完整 |
| 配置 | 确认 defconfig、product config、分区配置、启动参数来自同一产品线 |
| 输出目录 | 确认 `out/`、`release/`、升级包目录没有混用旧产物 |

## 3. 标准构建闭环

通用构建顺序：

```bash
rtk make -j8 all
rtk make install
```

项目支持单应用目标时，优先用单目标缩小问题：

```bash
rtk make -j8 <target>_app_all
```

构建失败时按以下顺序定位：

1. 看首个 error，不从最后一个汇总错误开始。
2. 判断是编译错误、链接错误、缺库、缺头文件、工具链错误还是生成器错误。
3. 对链接错误检查库顺序、静态库依赖和 `--start-group/--end-group`。
4. 对配置错误检查芯片、产品、板级配置和 defconfig 是否匹配。
5. 对生成器错误检查输入 proto、nanopb、代码生成工具版本。

## 4. 产物核对

构建通过不等于可交付。至少核对：

| 层级 | 核对内容 |
| --- | --- |
| 应用产物 | 主程序、daemon、cmd_server、工具程序是否生成 |
| 动态库 | 运行依赖库是否进入目标 rootfs 或 release |
| 配置 | ini/json/bin/IQ/model/资源文件是否随包安装 |
| 启动脚本 | daemon 或 init 脚本是否指向正确路径 |
| 版本信息 | APP、SDK、配置和升级包版本是否一致 |

建议保留一个产物清单：

```text
build_id:
git_rev:
sdk_version:
chip:
product:
app_binaries:
config_files:
model_or_iq_files:
release_path:
```

## 5. 烧录与启动检查

烧录前：

1. 确认镜像来源、版本号、目标板型号。
2. 确认分区表与镜像大小匹配。
3. 确认 boot、kernel、rootfs、customer 分区是否来自同一构建批次。
4. 现场烧录工具、USB/SD/网口路径按项目 SOP 执行。

首次启动后：

1. 看串口启动链：Boot -> Kernel -> rootfs -> init。
2. 看关键进程：daemon、cmd_server、主业务进程。
3. 看设备节点：sensor、audio、mtd/mmc、uart、i2c、gpio。
4. 看配置加载：产品模式、校准参数、网络参数、日志等级。
5. 看核心 smoke：启动、拍照/录像、音频、网络、诊断命令。

## 6. OTA 与回滚检查

OTA 相关问题先拆成四段：

| 阶段 | 检查点 |
| --- | --- |
| 打包 | 包格式、manifest、版本号、签名、压缩方式 |
| 传输 | 文件大小、hash、断点续传、存储空间 |
| 写入 | 分区映射、写入偏移、坏块、权限 |
| 切换 | boot flag、回滚标记、首次启动确认 |

失败时先保留：

1. 升级包文件名、大小、hash。
2. 当前版本和目标版本。
3. 分区表、升级日志、bootloader 日志。
4. 失败阶段和返回码。
5. 是否进入回滚或半升级状态。

## 7. 常见误区

1. 只跑 `make all` 不跑 `make install`，导致 release 中仍是旧产物。
2. 只替换应用二进制，不同步依赖库和配置。
3. 同一目录混入不同 SDK 或不同产品线产物。
4. 只看 APP 日志，不看 boot、kernel、daemon 和 cmd_server。
5. 升级失败后继续多次覆盖写入，破坏第一现场证据。

## 8. 验证方式

最小验证闭环：

```bash
rtk make -j8 all
rtk make install
```

设备侧至少确认：

1. 系统可启动到业务进程。
2. 关键进程在线。
3. 核心功能 smoke 通过。
4. 诊断入口可执行。
5. 日志中无新增的启动阻断错误。

若不能执行设备验证，文档或问题单必须明确写出缺失原因和剩余风险。
