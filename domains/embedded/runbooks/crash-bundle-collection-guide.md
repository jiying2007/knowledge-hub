---
title: 崩溃材料一键打包指南
doc_type: runbook
knowledge_type: process
maturity: verified
status: active
owner: team-core
created: 2026-05-15
last_updated: 2026-05-15
tags: [crash, bundle, core, debug]
related: [core-dump-capture-guide.md, core-binary-match-verification-guide.md]
validation_refs: [tools/debug/collect-crash-bundle.sh, tools/debug/core-env-snapshot.sh]
---

# 1. 目的

统一崩溃排障资料格式，减少“材料不全导致无法复盘”问题。

# 2. 打包内容

默认包含：

1. `core` 文件
2. `*.debug.full` 符号文件
3. 环境快照（脚本自动生成）
4. 可选 `dmesg` 与额外附件

# 3. 操作步骤

```bash
rtk bash tools/debug/collect-crash-bundle.sh \
  --bin out/arm/app/prog_pcr02.debug.full \
  --core out/arm/app/core-th_0x283855-913-12 \
  --dmesg out/arm/app/dmesg.tail.txt \
  --extra out/arm/app/asan.log \
  --out out/arm/app/crash-bundles
```

输出：

1. `bundle-.../` 目录
2. `bundle-....tar.gz` 归档文件

# 4. 交付建议

提交问题单时附：

1. `tar.gz` 包
2. 复现步骤
3. 崩溃时间
4. 当前根因假设

# 5. 失败处理

1. 参数缺失：先补 `--bin`、`--core`
2. 文件不存在：确认路径来自同一构建输出目录
3. 包体过大：允许单独压缩 `core`，但必须保留原始文件名
