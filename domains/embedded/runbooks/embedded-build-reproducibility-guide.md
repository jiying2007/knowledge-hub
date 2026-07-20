---
title: 嵌入式构建可复现指南
doc_type: runbook
knowledge_type: process
maturity: draft
status: archived
searchable: false
owner: team-core
created: 2026-05-18
last_updated: 2026-05-18
tags: [embedded, build, reproducibility, release]
related: [sigmastar-sdk-upgrade-playbook.md, ../standards/release-versioning-guide.md, ../standards/embedded-artifact-provenance-standard.md]
validation_refs: [../../scripts/generate-release-manifest.sh, ../../scripts/check-release-manifest.sh]
---

# 背景

嵌入式问题经常无法复现，是因为源码、工具链、SDK、rootfs、模型、配置和实际烧录产物无法对应。本文定义构建快照与 release manifest 的最小要求。

# 前置条件

1. 构建机时间同步。
2. 工具链路径、版本和 checksum 可记录。
3. SDK、rootfs、模型、配置不混用未记录来源。
4. 发布目录只包含本次构建产物，不混入历史残留。

# 操作步骤

## 1. 记录源码状态

```bash
git status --short --branch
git rev-parse HEAD
git submodule status --recursive
```

若存在未提交改动，发布记录必须说明 diff 来源，否则不得声明可复现。

## 2. 记录工具链状态

```bash
${CROSS_COMPILE:-arm-linux-gnueabihf-}gcc --version
file out/arm/app/prog_pcr02.debug.full
readelf -h out/arm/app/prog_pcr02.debug.full | sed -n 1,40p
```

## 3. 生成发布 manifest

```bash
rtk bash scripts/generate-release-manifest.sh --root out/arm/app --out out/arm/app/release-manifest.csv
rtk bash scripts/check-release-manifest.sh --manifest out/arm/app/release-manifest.csv
```

manifest 至少记录相对路径、大小、SHA256 和修改时间。

## 4. 记录运行依赖

```bash
rtk bash tools/debug/audit-binary-deps.sh --bin out/arm/app/prog_pcr02.debug.full --sysroot out/arm/target --out out/arm/app/binary-deps.txt
```

若存在缺失库，必须判断是目标板系统库、延迟加载库，还是发布遗漏。

# 回滚方案

1. 使用旧 release manifest 校验回滚包完整性。
2. 保留失败构建 manifest，避免后续误复用。
3. 不用“目录名称相同”判断产物一致，必须用 hash。

# 验证记录

每次 release 至少保存：

1. `release-manifest.csv`。
2. `binary-deps.txt`。
3. 构建命令与环境快照。
4. smoke 验证记录。
