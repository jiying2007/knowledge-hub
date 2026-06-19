# Knowledge Hub manual entry default dates 2026-06-19

## 结论

`knowledge-new.sh` 现在会在可复制草稿中自动填入默认日期：

- `created_at` / `updated_at` / `checked_at`：当前 UTC 日期。
- `review_after`：当前 UTC 日期后三个月。

维护者仍可在落盘前按 owner 或 review cycle 要求修改这些日期。该能力只减少手工占位符替换，不自动创建或修改文件。

后续增强：`knowledge-hub-manual-entry-owner-override-20260619` 增加 `--owner <owner>`，减少所有新增条目默认落到单一 owner 的维护瓶颈。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| MDD-001 | 人工新增向导的 registry 和 migration 草稿使用 `<YYYY-MM-DD>` 占位符。 | 人工复制时容易漏替换日期，导致 registry date gate 失败或复核周期缺失。 | 自动生成默认 ISO 日期。 |
| MDD-002 | review cycle 默认缺失会增加维护者决策成本。 | 新条目可能没有明确复核时间。 | `review_after` 默认按三个月后生成，仍允许人工修改。 |
| MDD-003 | 日期默认行为需要可回归。 | 后续改动可能重新引入日期占位符。 | 新增 `manual-entry-default-dates` 回归场景。 |

## 决策

- 日期默认只出现在只读草稿中，不自动写入仓库。
- 使用 UTC 日期，避免本地时区导致同一会话内日期不一致。
- 若 `date -d '+3 months'` 不可用，`review_after` 回退为当天日期，仍保持合法 ISO 日期。
- 不增加必填参数，保持人工新增入口低复杂度。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-new.sh --kind decision --domain governance --id governance-date-defaults --path governance/date-defaults.md` | 0 | 通过；registry 和 migration 草稿输出默认 ISO 日期，不再保留日期占位符 | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-default-dates-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；10 个回归场景全部 pass，包含新增 `manual-entry-default-dates` 场景 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manual-entry-default-dates-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manual-entry-default-dates-20260619` |

## 边界

- 不自动创建正文、registry、migration 或 index。
- 不替 owner 决定 review cycle；默认日期只是可编辑草稿。
- 不修改 PCR02 源项目 docs。
- 不关闭 owner gate，不生成 owner decision。
- 不启用自动化，不写 memory。
