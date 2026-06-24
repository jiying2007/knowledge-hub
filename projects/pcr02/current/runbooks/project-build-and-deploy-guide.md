---
title: PCR02 构建与部署手册
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-13
last_updated: 2026-05-13
tags: [build, deploy, runbook]
related: [../architecture/project-overview-design.md, ../architecture/module-catalog.md]
validation_refs: [Makefile, build/build.mk, app_product_test/dep.mk, pcr02/pcr02.mk]
---

# PCR02 构建与部署手册

## 1. 适用范围

- 本手册适用于当前仓库标准构建链（`Makefile` + `build/*.mk`）。
- 目标产物包含：`prog_cli`、`prog_cmd_server`、`prog_daemon`、`prog_product_test`、`prog_ota`、`prog_pcr02`。

## 2. 构建前检查

1. 工具链与 `PROJ_ROOT/CHIP/PRODUCT/TOOLCHAIN/TOOLCHAIN_VERSION` 环境可用。
2. `libs/3rdparty` 与 `libs/arm/libs/glibc/11.1.0/static` 已就绪。
3. `modules/proto` 与 `modules/proto_c` 生成工具（`protoc`/nanopb）可执行。

模块治理边界（执行本手册时默认）：

1. `modules` 仅纳管：`hdi/api/app/sensor/proto/proto_c`。
2. 其他模块即使出现在依赖链中，也视为外部团队交付二进制依赖。
3. `pcr02` 为公共主应用，负责统一集成这些依赖。

## 3. 常用命令

全量构建：

```bash
rtk make -j8 all
```

安装装配：

```bash
rtk make install
```

单应用构建（示例）：

```bash
rtk make -j8 cli_app_all
rtk make -j8 cmd_server_app_all
rtk make -j8 daemon_app_all
rtk make -j8 app_product_test_app_all
rtk make -j8 pcr02_app_all
```

清理：

```bash
rtk make clean
```

## 4. 产物路径

- 编译产物：`out/<arch>/app/`
- release 装配目录：`release/`
- install 复制目标：`$(PROJ_ROOT)/release/chip/.../release/bin/robot_pcr02/`

## 5. 构建特性与注意点

1. `DEBUG` 位控制 `DEBUG_ASAN`：`DEBUG&256` 或 `DEBUG&1` 时进入 debug 产物路径。
2. 白名单外模块（示例：`wifi_manager`）若参与构建，按外部依赖链处理，不纳入本仓库源码治理。
3. `app_product_test` 链接 `modules/proto_c`，并补充 OpenCV 依赖顺序避免静态链接缺符号。
4. `pcr02` 同时链接大量预编译模块库与第三方库，链接顺序敏感（已有 `--start-group/--end-group`）。

## 6. 部署与进程检查

目标机关键进程：

- `/customer/bin/prog_daemon`
- `/customer/bin/prog_cmd_server`
- `/customer/bin/prog_pcr02` 或 `/customer/bin/prog_product_test`

模式配置：

- `daemon.ini` 中 `INFO.Mode` 决定 APP/PRODUCT_TEST。

## 7. 故障定位入口

- 构建期：优先看 `make` 首个错误和对应 `dep.mk/lib.mk`。
- 运行期：先看 `daemon` 进程拉起状态，再看 `cmd_server` IPC，再看 `pcr02` 模块初始化日志。
- ASAN 相关问题按 `$EMBEDDED_KNOWLEDGE_HOME/docs/runbooks/asan-debug-guide.md` 执行。
