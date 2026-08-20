---
id: embedded-x5-sdk-download-20260805
title: X5 SDK 下载说明（脱敏版）
kind: runbook
domain: embedded
path: domains/embedded/runbooks/x5-sdk-download.md
scope: team-general
visibility: team-internal
status: reviewing
owner: team-core
source:
  type: user-provided-notice
  from: 2026-08-05 用户提供的 D-Robotics X5 SDK 下载通知，已删除认证信息
  source_sha256: 2a8c2d8f9ccf1d257b0cd9254c1a9d564e0078356694bac57ad9f5c1547cb781
review_after: '2026-11-05'
review_status: manual-entry-pending-review
content_review_status: pending
evidence_validation_status: pending
promotion: none
promotion_decision: none; capture does not authorize active promotion or owner decision
tags:
- x5
- sdk-download
- credential-hygiene
- ftp
validation_refs:
- domains/embedded/runbooks/x5-sdk-download.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
evidence_strength: manual-entry-validation-pending
evidence_refs:
- domains/embedded/runbooks/x5-sdk-download.md
- rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
created_at: '2026-08-05'
updated_at: '2026-08-05'
generated_by_ai: true
ai_role: drafted
ai_model_or_tool: Codex
ai_generated_at: '2026-08-05'
manual_validation_pending: true
summary_zh: 记录 X5 SDK 发布入口、FTP 目录、V1.1.2 下载路径、交互式 wget 模板和下载后验证方法；真实认证信息已排除，外部服务尚未联网验证。
primary_language: zh-CN
source_language: zh-CN
translation_status: not-required
terminology_status: pending-review
aliases:
- X5 SDK 下载说明（脱敏版）
related:
- indexes/obsidian-home.md
---

# X5 SDK 下载说明（脱敏版）

- 文档状态：下载入口由用户提供，尚未独立联网验证
- 适用芯片：D-Robotics X5
- 当前记录版本：`LNX6.1.83_PL5.1_V1.1.2`
- 信息接收日期：2026-08-05
- 最后核对日期：2026-08-05
- 安全级别：仓库内不得保存真实账号、密码或带凭据的下载 URL

## 1. 下载入口

SDK 下载说明和版本清单：

```text
http://sdk.d-robotics.cc/sdk_release
```

FTP 服务地址：

```text
ftp://sdk.d-robotics.cc
```

上述 HTTP 和 FTP 均不提供传输加密。使用前应优先向供应商确认是否提供 HTTPS、FTPS、SFTP、VPN 或其他受保护的下载通道。必须使用 FTP 时，只能在受信网络中操作，并避免复用重要密码。

## 2. 凭据管理

供应商为项目提供了专用下载账号，但真实账号和密码属于认证信息，已从本文和 Knowledge Hub 归档中排除。

使用要求：

- 从供应商平台、企业密码管理器或其他批准的安全渠道获取凭据；
- 不要把密码写入 Markdown、脚本、Git、Knowledge Hub、工单或聊天记录；
- 不要把密码直接写入命令行参数、下载 URL 或可被其他用户读取的环境文件；
- 如凭据曾以明文出现在聊天或日志中，应立即轮换；
- 下载完成后清理临时凭据，并检查 shell history、进程日志和 CI 日志；
- 不得将真实凭据提交到本仓库。

## 3. FTP 目录

X5 芯片数据手册和硬件参考设计：

```text
/X5_datasheet_and_design_guide
```

X5 Linux SDK V1.1.2：

```text
/X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2
```

下载完成后的预期本地目录：

```text
X5_datasheet_and_design_guide/
X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2/
```

## 4. 脱敏下载模板

以下模板不会保存真实用户名，密码由 `wget` 交互询问：

```bash
read -r -p "SDK FTP user: " SDK_FTP_USER

wget --user="$SDK_FTP_USER" --ask-password \
  --recursive \
  --no-host-directories \
  ftp://sdk.d-robotics.cc/X5_datasheet_and_design_guide

unset SDK_FTP_USER
```

下载 X5 Linux SDK：

```bash
read -r -p "SDK FTP user: " SDK_FTP_USER

wget --user="$SDK_FTP_USER" --ask-password \
  --recursive \
  --no-host-directories \
  ftp://sdk.d-robotics.cc/X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2

unset SDK_FTP_USER
```

注意：`--ask-password` 只能避免密码进入命令行和 shell history，不能解决 FTP 协议本身明文传输凭据的问题。

## 5. 下载后验证

先检查目录和文件规模：

```bash
du -sh X5_datasheet_and_design_guide
du -sh X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2
find X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2 -maxdepth 2 -type d -print
```

验证交付包随附的 MD5 文件，例如 BSP 源码：

```bash
cd X5_LNX_SDK/LNX6.1.83_PL5.1_V1.1.2/board_support_package
md5sum -c platform_source_code.tar.gz.md5sum
```

若供应商提供 SHA-256、签名文件或发布清单，应优先使用强校验；MD5 只能用于发现意外损坏，不能证明文件未被恶意篡改。

还应确认：

- Release Notes 中的版本与目标版本一致；
- 固件、源码、用户手册和软件工具目录完整；
- 下载过程中没有 `failed`、`timed out`、`permission denied` 或 `login incorrect`；
- 不完整下载应从可信入口重新获取，不手工拼接损坏包。

## 6. 与首次启动 Runbook 的关系

SDK 下载完成后，首次启动和固件恢复步骤见 [X5 EVB V2P0 首次启动与固件恢复 Runbook](x5-evb-v2p0-first-boot.md)。

首次启动优先验证开发板出厂 eMMC，不要求先编译或重新刷写 SDK。

## 7. 来源、脱敏与验证状态

来源：2026-08-05 用户提供的 D-Robotics X5 SDK 下载通知。

归档脱敏处理：

- 删除真实 FTP 用户名；
- 删除真实 FTP 密码；
- 删除包含真实用户名和密码的完整命令；
- 保留公开服务入口、FTP 目录、版本号和安全下载模板；
- 未复制原始聊天消息或认证信息。

当前验证状态：

- 已确认目标版本与本仓现有 SDK 目录一致；
- 已确认本仓存在数据手册、硬件参考设计和 V1.1.2 SDK 目录；
- 未访问外部下载页；
- 未连接 FTP；
- 未验证账号有效性、服务可用性或远端文件完整性。

因此，本记录是脱敏下载 runbook，不是外部服务可用性证明。
