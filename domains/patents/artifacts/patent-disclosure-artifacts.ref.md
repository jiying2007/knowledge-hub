# Patent Disclosure Artifact References

## 摘要

本文件登记 source `patent-disclosure` 中非 Markdown 附件的 Hub vault 清单。附件正文已按硬迁移计划复制到 `artifacts/vault/patent-disclosure`；长期身份以 vault 相对路径、`sha256`、`size`、迁移 manifest 和 retired `origin_path` provenance 为准。

## 制品身份

- source_id：`patent-disclosure`
- hub_source_path：`sources/patent-disclosure`
- canonical_target：`domains/patents/archive/patent-disclosure`
- artifact_target：`artifacts/vault/patent-disclosure`
- origin_path：`~/embedded/patent_disclosure`（retired provenance only）
- manifest：`artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl`
- hard_migration_manifest：`artifacts/manifests/source-hard-migration-20260624.jsonl`
- rows：181
- artifact_type：`png=153`、`docx=12`、`doc=7`、`pdf=6`、`rar=3`
- total_size_bytes：`23901650`

## 权威来源

Knowledge Hub 的 `artifacts/vault/patent-disclosure` 是迁移后附件保管位置；旧源目录只用于删除前 provenance 和差异审计，不再作为权威读取入口。

## 使用边界

- 可用于确认专利图片、文档附件、PDF 和压缩包是否存在于 Hub vault。
- 不代表附件已完成法律复核、公开授权或正式提交。
- `.git/**` 和 `.gitignore` 是源目录版本控制元数据，不作为专利附件登记。
- 如需新增或替换附件正文，必须新增归档评估，明确敏感信息、版权、体积、owner review 和 vault 写入证据。

## 验证

```bash
rtk test -d artifacts/vault/patent-disclosure
rtk bash tools/knowledge-check.sh --dry-run --json
```

如需重新生成同名 manifest，必须先确认 Hub vault 变化、retired origin provenance 和 owner review，再显式使用 `--force`。日常复核默认只读检查，不覆盖既有证据。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：Hub vault 是否完整、附件引用 manifest 是否需要 delta 更新、是否有附件需要独立法律或专利流程复核。
