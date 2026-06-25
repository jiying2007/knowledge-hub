# Engineering Archive

本目录是 PCR02 工程归档区。新增工程归档应写入 `projects/pcr02/archive/engineering-archive/pcr02/`，不得写回外部旧目录。

## Structure

```text
projects/pcr02/archive/engineering-archive/
  README.md
  pcr02/
    README.md
    ota-release/
    partition-storage/
    ubifs-squashfs/
    boot-flash/
    hardware-power/
    runtime-io/
    validation/
    source-audit/
```

## 规则

- 保留可复用决策、证据、命令、发布说明和验证指南。
- 默认不保存完整 raw 串口日志；只提取关键证据片段。
- 不保存凭证、私钥、token 或运行时 secret。
- 默认不复制大型 release binary；记录路径、大小、hash 和 NAS 位置。
- 复杂工作流使用主题目录和局部 `README.md`。
- 小型自包含记录使用单个 Markdown 文件。

## Projects

- [PCR02](pcr02/README.md)
