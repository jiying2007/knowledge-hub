---
id: embedded-x5-sdk-v1-1-2-source-build-20260806
title: X5 SDK V1.1.2 源码构建与交接 Runbook
kind: runbook
domain: embedded
path: domains/embedded/runbooks/x5-sdk-v1.1.2-source-build.md
scope: team-general
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: source-project
  from: 2026-08-05 至 2026-08-06 的 X5 V1.1.2 成功构建、交接文档与自动化验证的脱敏摘要
  source_sha256: 70aaf7c1eb1ba185a98b6d4fc6b8a99eec689dc35722f4f04c1bd0eec3a523a2
  temporary_source_retained: false
review_after: '2026-11-06'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- x5
- sdk-build
- runbook
validation_refs:
- domains/embedded/runbooks/x5-sdk-v1.1.2-source-build.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- domains/embedded/runbooks/x5-sdk-v1.1.2-source-build.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-06'
updated_at: '2026-08-06'
generated_by_ai: true
ai_role: summarized
ai_model_or_tool: Codex
ai_generated_at: '2026-08-06'
manual_validation_pending: true
summary_zh: X5 SDK V1.1.2 的固定 27 项目源码基线、Ubuntu 环境搭建、EVB eMMC release 全量构建、镜像校验和工程师交接流程已验证，板级烧录待完成。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- X5 SDK V1.1.2 源码构建与交接 Runbook
related:
- indexes/obsidian-home.md
---

# X5 SDK V1.1.2 源码构建与交接 Runbook

- captured_at：2026-08-06
- last_verified：2026-08-06
- 状态：主机构建与交接工具已验证；开发板烧录和启动待验证

## 目标

从受控的内部 Git manifest 同步 D-Robotics X5 Linux SDK `LNX6.1.83_PL5.1_V1.1.2`，安装 Ubuntu 主机依赖和 ARM GNU Toolchain 11.3.Rel1，使用 X5 EVB eMMC release 配置完成全量构建，并验证原始与 sparse 全盘镜像。

## 固定基线

- manifest 分支：`internal/v1.1.2-x5-4467`
- manifest commit：`9b1e8ef20c56304db60ce89159c4eaa0e057264f`
- 项目数量：27
- `prebuilts/hbre` 补丁 commit：`85ef06965db7fa79888029217e3a30d44abac94a`
- board config：`board_x5_evb_release_config.mk`
- 工具链压缩包 MD5：`9f84a51fb3e05ea4ad9c390242389226`

## 可复现流程

1. 在 Ubuntu 18.04/20.04/22.04 x86_64 主机准备 Git、Python 3、sudo、tar 和受信的 Android repo launcher，至少保留 25 GiB 空闲磁盘。
2. 通过安全的运行时凭据机制访问内部 Git 服务；不得把账号、密码、令牌或认证 URL 写入 Git、文档或日志。
3. 对固定 manifest 执行 `repo init` 与 `repo sync -c -j4 --no-clone-bundle`。
4. 验证 manifest HEAD、27 个项目和补丁 commit。
5. 执行供应商 `build/install_host_deps.sh`；Ubuntu 20.04/22.04 安装 `cryptography==40.0.2`。
6. 校验工具链压缩包并解压至 `/opt/arm-gnu-toolchain-11.3.rel1-x86_64-aarch64-none-linux-gnu`。
7. 执行 `./bd.sh lunch board_x5_evb_release_config.mk`，然后执行 `./bd.sh`。
8. 要求日志终态包含 `Congratulations, the build succeeded`，并验证 `out/product` 中的全盘、分区和 `uart_usb` 产物。
9. 计算本次 `emmc_disk.img` 与 `emmc_disk.simg` 的 SHA-256；不同构建可能因时间戳产生不同哈希，不能强制复用旧值。

## 已验证证据

- Ubuntu 20.04 x86_64 主机全量构建通过，内核为 `6.1.83-DR-PL5.1_V1.1.2`。
- 原始镜像大小 1,225,568,256 bytes，验证构建 SHA-256 为 `95896bbb38784172de834f82d6670b5c5176754d6cf4bca6644a51872f464fa6`。
- sparse 镜像大小 427,697,052 bytes，验证构建 SHA-256 为 `aaf745503d49ce087c13d95991f6d66286543978a5c6f42447419e46233fbc4f`。
- 工程工具的单元测试、Python 编译检查、shell 语法、非仓库 cwd help、完整流程 dry-run 和真实产物校验通过。
- 首轮测试发现 Python 3.8 不支持 `hashlib.md5(usedforsecurity=False)`，改用兼容调用后全部测试通过。

## 镜像布局与边界

供应商 pack 流程跳过 `private` 和 `userdata`，原始镜像在 `app` 分区末尾截断，因此离线 GPT 工具会提示备用 GPT 缺失。不要脱离供应商烧录流程自行修复 GPT。主机构建通过不代表板级通过，仍需在真实 EVB 上验证 BootROM、U-Boot、Linux、eMMC、网络或 ADB。

## 归档边界

本记录不包含内部主机地址、账号、密码、令牌、认证过程、原始日志或固件二进制。AI Toolchain、软件工具和固件是否写入 NAS 由开发者人工决定，不自动执行。memory candidate：否，这是项目特定 runbook。
