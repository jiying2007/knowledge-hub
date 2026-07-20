---
title: 嵌入式制品来源追溯规范
doc_type: standard
knowledge_type: guideline
maturity: draft
status: archived
searchable: false
owner: team-core
created: 2026-05-18
last_updated: 2026-05-18
tags: [artifact, provenance, release, manifest, security]
related: [release-versioning-guide.md, repository-structure-guide.md, ../runbooks/embedded-build-reproducibility-guide.md, ../runbooks/sigmastar-archive-artifact-guide.md]
validation_refs: [../../scripts/generate-release-manifest.sh, ../../scripts/check-release-manifest.sh, ../../scripts/check-artifacts.sh]
---

# 背景

固件、模型、配置、动态库和调试符号如果无法追溯来源，会导致现场问题无法复现、误烧录、误回滚和供应链风险。本文定义进入团队知识库或发布包的制品追溯最低标准。

# 规范内容

## 1. 必须记录的来源字段

每个发布制品至少记录：

1. 相对路径。
2. 文件大小。
3. SHA256。
4. 生成时间或归档时间。
5. 源码 commit 或外部来源标识。
6. 构建命令或生成流程。
7. 适用平台和限制。

## 2. 禁止进入 Git 的内容

1. 原始 SDK 压缩包。
2. 未脱敏客户日志。
3. core dump、超大二进制包、现场完整镜像。
4. 私有密钥、token、账号、内网凭据。
5. 来源不明的模型和脚本。

这些内容只能进入受控制品存储，并在 Git 中保留 manifest 或索引。

## 3. 模型与配置追溯

AI 模型必须额外记录：

1. 模型格式和 runtime。
2. 输入尺寸、颜色格式、normalize 参数。
3. 类别表版本。
4. 量化方式。
5. 训练或转换来源。
6. 与应用配置的匹配关系。

## 4. 调试符号追溯

`*.debug.full`、strip 后 binary、core dump 必须能配对验证。不能用“文件名相似”作为匹配依据，必须结合 build-id、file 信息、gdb 载入结果或 manifest hash。

# 约束与例外

1. 临时现场救火可先保存到 `/tmp` 或受控 NAS，但事后必须补 manifest。
2. 第三方闭源二进制若无法获取源码，必须记录供应商、版本和接收时间。
3. 安全敏感材料不得通过知识库归档，只能保存脱敏摘要。

# 验证方式

1. 发布目录执行 `rtk bash scripts/generate-release-manifest.sh`。
2. 发布前执行 `rtk bash scripts/check-release-manifest.sh`。
3. 仓库执行 `rtk bash scripts/check-artifacts.sh` 和 `rtk bash scripts/check-secrets.sh`。
4. 二进制执行 `rtk bash tools/debug/audit-binary-deps.sh`。

# 参考与追溯

- `docs/runbooks/embedded-build-reproducibility-guide.md`
- `docs/runbooks/sigmastar-archive-artifact-guide.md`
- `docs/standards/release-versioning-guide.md`
