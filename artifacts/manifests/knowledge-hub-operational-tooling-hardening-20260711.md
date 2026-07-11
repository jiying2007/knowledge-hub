# Knowledge Hub operational tooling hardening 2026-07-11

## 摘要

本次增强把长期运营建议落为可执行工具：changed-only orphan 文件检查、reviewing 周期 triage、full regression 趋势摘要，以及 health summary 首屏聚合。

该增强只作用于 Knowledge Hub 控制面，不生成 owner decision、不关闭 owner gate、不提升 active、不写 memory、不修改源项目。

## 范围

| 项 | 结果 | 边界 |
| --- | --- | --- |
| Changed-only orphan check | 新增 `tools/knowledge-orphan-files.sh`，默认只检查本次变更中的正文 Markdown 是否进入 registry | `--all` 只作历史长尾 advisory，不作为 mature blocker |
| Reviewing triage | 新增 `tools/knowledge-reviewing-triage.sh`，按 bucket/action 输出 reviewing 队列 | 不 archive、不 active promotion、不代签 owner |
| Regression trend | 新增 `tools/knowledge-regression-trend.sh`，压缩 full/quick regression JSON 的数量和慢测趋势 | 不保存 full regression 原始大 JSON |
| Health summary | `tools/knowledge-health-summary.sh` 接入 changed orphan 和 reviewing triage | changed orphan 缺口可阻断日常健康摘要 |
| PCR02 orphan 收口 | 登记 `pcr02_evt2_mcu_soc_contract_index_20260711.md` | 保持 reviewing，作为 source-derived contract index，不作为板级验证或 release 证明 |

## 运营命令

```bash
rtk bash tools/knowledge-health-summary.sh --json --as-of 2026-07-11
rtk bash tools/knowledge-orphan-files.sh --json
rtk bash tools/knowledge-reviewing-triage.sh --json --as-of 2026-07-11
rtk bash tools/knowledge-regression-trend.sh --from-json <knowledge-regression-output.json> --json
```

需要重新采集趋势时使用：

```bash
rtk bash tools/knowledge-regression-trend.sh --run --suite full --as-of 2026-07-11 --json
```

## 非目标

- 不把历史工程归档长尾全部强制逐条 registry 化。
- 不把 reviewing 条目自动 archive 或 active。
- 不把 ST77912、PCR02 camera、MCU/SoC contract 候选当作 owner-signed 决策。
- 不写 `~/.codex/memories`。
- 不 push、merge、rebase、tag 或 release。

## 后续节奏

- 每周运行 health summary 和 reviewing triage。
- 每次新增项目正文后运行 changed-only orphan check。
- full regression 做终态收口时同步生成 compact trend 摘要，避免长期只保存大段 JSON。
