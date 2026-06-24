# Patent Disclosure Copy-First Applied 2026-06-19

## 目标

把已登记 source `patent-disclosure` 中可作为长期文本资产维护的 Markdown 专利披露材料迁入 Knowledge Hub，并把图片、Word、PDF、RAR 等非文本附件登记为 artifact reference，避免把大型或二进制附件复制进文本知识层。

## 问题地图

| ID | 问题 | 风险 | 处理 |
| --- | --- | --- | --- |
| PDC-001 | `patent-disclosure` 已在 source registry 中登记，但正文材料仍散落在源目录。 | 专利草稿、权利要求和检索优化说明难以进入长期治理。 | 将 10 个 Markdown 文件 copy-first 到 `domains/patents/archive/patent-disclosure/`。 |
| PDC-002 | 源目录包含大量图片、doc、pdf、rar 等附件。 | 直接复制会让知识层变大、难审、难做 secret scan。 | 生成 `patent-disclosure-artifact-ref-20260619.jsonl`，只登记 `uri`、`sha256`、`size` 和类型。 |
| PDC-003 | 专利材料可能包含草稿、对话记录和代理前文本。 | 误读为法律终稿或已授权专利会带来决策风险。 | Registry 状态保持 `reviewing` 或 archive-only，不声明法律终稿，不进入 active。 |

## 迁移范围

- Source id：`patent-disclosure`
- Source root：`~/embedded/patent_disclosure`
- Markdown target root：`domains/patents/archive/patent-disclosure`
- Markdown manifest：`artifacts/manifests/patent-disclosure-copy-first-dry-run-20260619.jsonl`
- Artifact reference manifest：`artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl`
- Markdown rows：10
- Artifact reference rows：181
- Artifact type counts：`png=153`、`docx=12`、`doc=7`、`pdf=6`、`rar=3`
- Artifact total size：`23901650` bytes

## 决策

- Markdown 正文采用 copy-first，保留源相对路径的文件名，便于与源目录核对。
- 非文本附件采用 artifact-ref，不复制附件正文，不把图片或二进制文件纳入文本知识层。
- `.git/**` 和 `.gitignore` 被视为源目录版本控制元数据，不作为专利材料登记。
- 本批次以 aggregate registry item 管理专利 Markdown 语料和附件引用清单，避免一次性维护 191 个细粒度条目造成维护瓶颈。
- 后续如某份专利披露需要进入 filing、legal review 或公开交付状态，必须新增独立 registry item、owner review、法律边界和证据链。

## 非目标

- 不修改 `~/embedded/patent_disclosure` 源目录。
- 不复制图片、doc、pdf、rar 等附件正文。
- 不声明任何材料为已提交、已公开、已授权或法律终稿。
- 不启用自动化。
- 不写入 `~/.codex/memories`。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
| --- | --- | --- | --- | --- | --- |
| `rtk bash tools/knowledge-copy-first-plan.sh --source-id patent-disclosure --target-prefix domains/patents/archive/patent-disclosure --bucket archive --owner leiwenjun --review-status patent-disclosure-copy-first-dry-run --source-status archived --id-prefix patent-disclosure-copyfirst --output artifacts/manifests/patent-disclosure-copy-first-dry-run-20260619.jsonl --json` | 0 | 生成 10 行 Markdown copy-first manifest；非 Markdown 附件被跳过。 | `artifacts/manifests/patent-disclosure-copy-first-dry-run-20260619.jsonl` | Knowledge Hub | patent-disclosure |
| `rtk bash tools/knowledge-artifact-ref-plan.sh --source-id patent-disclosure --id-prefix patent-disclosure-artifact --output artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl --json` | 0 | 生成 181 行 artifact-ref manifest；`.git/**` 和 `.gitignore` 不纳入专利附件。 | `artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl` | Knowledge Hub | patent-disclosure-artifacts |
| `rtk bash tools/knowledge-copy-first.sh --manifest artifacts/manifests/patent-disclosure-copy-first-dry-run-20260619.jsonl --dry-run --json` | 0 | 校验 10 个源 Markdown hash/size、目标 bucket 和目标不存在，`status=planned`。 | `artifacts/manifests/patent-disclosure-copy-first-dry-run-20260619.jsonl` | Knowledge Hub | patent-disclosure-copyfirst |
| `rtk bash tools/knowledge-copy-first.sh --manifest artifacts/manifests/patent-disclosure-copy-first-dry-run-20260619.jsonl --apply --json` | 0 | 复制 10 个 Markdown 文件到 patents archive，`status=applied`。 | `domains/patents/archive/patent-disclosure` | Knowledge Hub | patent-disclosure-markdown-corpus-20260619 |
| `rtk bash tools/knowledge-copy-first.sh --manifest artifacts/manifests/patent-disclosure-copy-first-dry-run-20260619.jsonl --verify-existing --json` | 0 | 复验 10 个目标文件 hash/size 与 manifest 匹配，`status=verified`。 | `domains/patents/archive/patent-disclosure` | Knowledge Hub | patent-disclosure-markdown-corpus-20260619 |

## 后续边界

- 专利披露材料进入正式提交流程前，必须补充 owner、法律复核状态、公开边界和版本冻结记录。
- 附件如需长期复制保存，必须单独评估体积、敏感信息、版权和 hash 证据，不得绕过 artifact-ref。
- 如果源目录后续变化，新增 delta manifest，不直接覆盖本批次 archive。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- validation_refs：`tools/knowledge-copy-first.sh --manifest artifacts/manifests/patent-disclosure-copy-first-dry-run-20260619.jsonl --verify-existing --json`
