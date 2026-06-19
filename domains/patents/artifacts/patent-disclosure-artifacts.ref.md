# Patent Disclosure Artifact References

## 摘要

本文件登记 source `patent-disclosure` 中非 Markdown 附件的引用清单。附件正文不复制到 Knowledge Hub；长期身份以 `source://patent-disclosure/<relative-path>`、`sha256` 和 `size` 为准。

## 制品身份

- source_id：`patent-disclosure`
- source_root：`/home/leiwenjun/embedded/patent_disclosure`
- manifest：`artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl`
- rows：181
- artifact_type：`png=153`、`docx=12`、`doc=7`、`pdf=6`、`rar=3`
- total_size_bytes：`23901650`

## 权威来源

源目录仍是附件正文的权威位置。Knowledge Hub 只维护引用清单，不维护二进制正文副本。

## 使用边界

- 可用于确认专利图片、文档附件、PDF 和压缩包是否存在于源目录。
- 不代表附件已完成法律复核、公开授权或正式提交。
- `.git/**` 和 `.gitignore` 是源目录版本控制元数据，不作为专利附件登记。
- 如需复制附件正文，必须新增归档评估，明确敏感信息、版权、体积和 owner review。

## 验证

```bash
rtk jq -c . artifacts/manifests/patent-disclosure-artifact-ref-20260619.jsonl
rtk bash tools/knowledge-check.sh --dry-run --json
```

如需重新生成同名 manifest，必须先确认源目录变化和 owner review，再显式使用 `--force`。日常复核默认只读检查，不覆盖既有证据。

## Review

- owner：`leiwenjun`
- review_after：`2026-09-19`
- 下一次复核内容：源目录是否仍可访问、附件引用 manifest 是否需要 delta 更新、是否有附件需要独立长期归档。
