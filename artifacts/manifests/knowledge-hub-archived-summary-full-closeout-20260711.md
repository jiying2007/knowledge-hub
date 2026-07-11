# Knowledge Hub Archived Summary Full Closeout 2026-07-11

## Scope

本记录收口 Knowledge Hub registry 中所有 archived `summary_zh` 缺口。摘要来源限定为 Hub 内已存在正文、ref 文件或目录身份，不读取源项目、不复制 raw log、不生成 owner decision。

## Result

- Backfilled archived items: 125
- Closeout artifact id: `knowledge-hub-archived-summary-full-closeout-20260711`
- Boundary: archived readability only; no active promotion, no owner gate closure, no memory write, no source project write.

## Batch Distribution

- `governance` / `audit`: 86
- `projects/pcr02` / `audit`: 17
- `projects/pcr02` / `project-current`: 11
- `codex` / `audit`: 3
- `projects/pcr02` / `decision`: 3
- `embedded` / `audit`: 1
- `patents` / `audit`: 1
- `patents` / `patent`: 1
- `projects/pcr02` / `artifact-ref`: 1
- `projects/pcr02` / `project-archive`: 1

## Verification

- `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics --as-of 2026-07-11`
- `rtk bash tools/knowledge-status.sh --strict --json --as-of 2026-07-11 --final-profile mature`
- `rtk bash tools/knowledge-final-gate.sh --json --final-profile mature --as-of 2026-07-11`
- `rtk bash tools/knowledge-regression.sh --json --suite full --as-of 2026-07-11`
