# Patent Disclosure Artifact References

## 摘要

本文件登记 source `patent-disclosure` 中非 Markdown 附件的身份清单。178 个可读附件已按硬迁移计划复制到 `artifacts/vault/patent-disclosure`，3 个 RAR 只保留外部引用 provenance；长期身份以 manifest 中的相对路径、`sha256`、`size`、`vault_presence` 和 retired `origin_path` 为准。

## 制品身份

- source_id：`patent-disclosure`
- hub_source_path：`sources/patent-disclosure`
- canonical_target：`domains/patents/archive/patent-disclosure`
- artifact_target：`artifacts/vault/patent-disclosure`
- origin_path：`~/embedded/patent_disclosure`（retired provenance only）
- manifest：`artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl`
- hard_migration_manifest：`artifacts/manifests/source-hard-migration-20260624.jsonl`
- identity_rows：181
- vault_present：178（`png=153`、`docx=12`、`doc=7`、`pdf=6`）
- external_reference_only：3 个 RAR；只保留 source URI、size 和 sha256，不在 Git vault 中
- vault_present_size_bytes：`15955434`
- identity_total_size_bytes：`23901650`（包含 3 个未落入 vault 的 RAR provenance）

## 权威来源

Knowledge Hub 的 `artifacts/vault/patent-disclosure` 是 178 个已落盘附件的保管位置；3 个 RAR 没有当前本地读取权威，旧源目录只作 retired provenance 和差异审计。

## 使用边界

- 可用于确认 178 个图片、文档附件和 PDF 存在于 Hub vault，并核对 path、size 和 sha256。
- 3 个 RAR 只属于 `external-reference-only` provenance；旧 origin 已退役，不能据此宣称本地附件仍可读取。
- 不代表附件已完成法律复核、公开授权或正式提交。
- `.git/**` 和 `.gitignore` 是源目录版本控制元数据，不作为专利附件登记。
- 如需新增或替换附件正文，必须新增归档评估，明确敏感信息、版权、体积、owner review 和 vault 写入证据。

## 验证

```bash
rtk test -d ~/knowledge-hub/artifacts/vault/patent-disclosure
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
```

如需重新生成同名 manifest，必须先确认 Hub vault 变化、retired origin provenance 和 owner review，再显式使用 `--force`。日常复核默认只读检查，不覆盖既有证据。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：Hub vault 是否完整、附件引用 manifest 是否需要 delta 更新、是否有附件需要独立法律或专利流程复核。
