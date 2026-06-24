# Engineering Archive Copy-First Applied 2026-06-19

## 目标

把已登记 source `engineering-archive` 中的 PCR02 历史工程归档落到 Knowledge Hub 项目归档域，作为 archive-only 长期资产保存，降低旧路径继续成为隐性知识源的风险。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| EAC-001 | `engineering-archive` 在 source inventory 中被列为 copy-first 候选，但尚未落地。 | 旧归档继续游离在 Knowledge Hub 外，迁移终态无法证明。 | 新增通用 `knowledge-copy-first-plan.sh`，生成可审查 JSONL manifest。 |
| EAC-002 | 既有 `knowledge-copy-first.sh` 只支持 `pcr02-project-docs`。 | 无法复用同一 hash/size 校验链路迁移其他已登记 source。 | 放宽为按 manifest 校验任意 registered source 的 copy-first 行，目标仍限制在 `domains/projects/pcr02/<bucket>/`。 |
| EAC-003 | PCR02 历史工程归档不应进入 current 或 team standard。 | 历史过程、session 和 memory candidate 可能被误读为当前事实。 | 全部复制到 `domains/projects/pcr02/archive/engineering-archive/`，registry aggregate item 使用 `archived`。 |

## 迁移范围

- Source id：`engineering-archive`
- Source root：`~/embedded/engineering_archive`
- Target root：`domains/projects/pcr02/archive/engineering-archive`
- Manifest：`artifacts/manifests/engineering-archive-copy-first-dry-run-20260619.jsonl`
- Rows：38
- Mode：copy-first archive-only

## 决策

- 本次迁移保留 source 相对路径结构，便于和旧归档互相核对。
- 迁移目标统一放入 PCR02 项目 archive，不进入 `current`、`decisions` 或 `domains/embedded/standards`。
- 对整个 archive corpus 登记一个 aggregate registry item，避免一次性维护 38 个细粒度条目造成维护瓶颈。
- 后续如某份历史归档需要提升为 decision、validation 或 runbook，必须另起 owner review 和独立 registry item。

## 非目标

- 不修改 `engineering-archive` 源文件。
- 不把 session、memory candidate 或历史排障过程提升为 active fact。
- 不启用自动化。
- 不写入 `~/.codex/memories`。
- 不把 PCR02 project-specific 内容提升到 `domains/embedded/standards`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-copy-first-plan.sh --source-id engineering-archive --target-prefix domains/projects/pcr02/archive/engineering-archive --bucket archive --owner team-core --review-status engineering-archive-copy-first-dry-run --source-status archived --id-prefix engineering-archive-copyfirst --output artifacts/manifests/engineering-archive-copy-first-dry-run-20260619.jsonl --json` | 0 | 生成 38 行 copy-first dry-run manifest，无 errors/warnings。 | `artifacts/manifests/engineering-archive-copy-first-dry-run-20260619.jsonl` | Knowledge Hub | engineering-archive |
| `rtk bash tools/knowledge-copy-first.sh --manifest artifacts/manifests/engineering-archive-copy-first-dry-run-20260619.jsonl --dry-run --json` | 0 | 校验 38 个 source hash/size、target bucket 和目标不存在，`status=planned`。 | `artifacts/manifests/engineering-archive-copy-first-dry-run-20260619.jsonl` | Knowledge Hub | engineering-archive-copyfirst |
| `rtk bash tools/knowledge-copy-first.sh --manifest artifacts/manifests/engineering-archive-copy-first-dry-run-20260619.jsonl --apply --json` | 0 | 复制 38 个文件到 PCR02 archive，`status=applied`。 | `domains/projects/pcr02/archive/engineering-archive` | Knowledge Hub | engineering-archive-pcr02-archive-corpus-20260619 |
| `rtk bash tools/knowledge-copy-first.sh --manifest artifacts/manifests/engineering-archive-copy-first-dry-run-20260619.jsonl --verify-existing --json` | 0 | 复验 38 个目标文件 hash/size 与 manifest 匹配，`status=verified`。 | `domains/projects/pcr02/archive/engineering-archive` | Knowledge Hub | engineering-archive-pcr02-archive-corpus-20260619 |

## 后续边界

- 如果要把其中某份历史归档提升为当前项目事实，必须新增独立条目、owner 决策和验证证据。
- 如果源归档后续变化，必须重新生成 dry-run manifest 或新增 delta manifest，不直接覆盖已有 Knowledge Hub archive。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- validation_refs：`tools/knowledge-copy-first.sh --manifest artifacts/manifests/engineering-archive-copy-first-dry-run-20260619.jsonl --verify-existing --json`
