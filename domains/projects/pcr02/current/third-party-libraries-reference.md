---
title: PCR02 第三方库引用基线
doc_type: standard
knowledge_type: guideline
maturity: verified
status: active
owner: team-core
created: 2026-05-13
last_updated: 2026-05-13
tags: [third-party, dependency, standard]
related: [../runbooks/project-build-and-deploy-guide.md, ../architecture/module-catalog.md]
validation_refs: [libs/3rdparty, build/app_3rdparty.mk, pcr02/pcr02.mk]
---

# PCR02 第三方库引用基线

## 1. 目的

统一记录仓库内第三方依赖目录和主要链接场景，避免“代码已引用但文档缺失”。

## 2. 第三方库目录基线（`libs/3rdparty`）

当前目录清单：

- `BehaviorTree`
- `aac`（`faac`/`faad`）
- `agora_sdk`
- `aiawaken`
- `aispeech`
- `audio`
- `bluez`
- `cJSON`
- `curl`
- `eigen`
- `fmt`
- `libabsl`
- `libevent`
- `libnl`
- `libsqlite`
- `libwebsockets`
- `libzmq`
- `live555`
- `lvgl`
- `mbedtls`
- `mp3`
- `mp4`
- `mqtt`
- `nanopb`
- `nlohmann_json`
- `opencv`
- `openssl`
- `protobuf`
- `spdlog`
- `ss_rtsp`
- `tlsf`
- `wifi`
- `wpa_client`
- `zbar`
- `zlib`
- `zxing`

## 3. 主要链接入口

- 通用应用（`cli/cmd_server/daemon/app_product_test/app_ota`）：
  - 由 `build/app_3rdparty.mk` 与 `build/app_sigmastar.mk` 统一注入 include/lib。
- 主业务应用（`pcr02`）：
  - 在 `pcr02/pcr02.mk` 明确声明高密度链接项（absl/protobuf/spdlog/fmt/openssl/opencv/mqtt/libnl 等）。
- 产测应用（`app_product_test`）：
  - 额外显式链接 `proto_c` 与 OpenCV 相关静态依赖补偿项。

## 4. 治理规则（强制）

1. 新增第三方库必须满足三同步：
   - 构建脚本同步（`*.mk`）
   - 文档同步（本文件）
   - 交付清单同步（若涉及 `MODULE_REL_LIB`）
2. 升级版本必须记录影响范围：
   - 影响应用
   - ABI/SONAME 变化
   - 回归验证命令
3. 删除第三方库前必须完成：
   - 反向引用扫描（源码+mk）
   - 链接验证
   - 运行验证

## 5. 备注

- `libs/arm/libs/glibc/11.1.0/static` 中的 `libtask/libiot/libai/libnavigation` 属于预编译业务模块，不计入第三方库统计，但必须纳入集成验证。
