# Source hard decommission 2026-06-25

本报告记录 Knowledge Hub 外部 source 退役状态的 2026-06-25 复核结果。

- paired_jsonl: `artifacts/manifests/source-hard-decommission-20260625.jsonl`
- status: `external-source-already-deleted` / `keep-runtime-input` / `keep-hub-native`
- registered_sources: 18
- delete_external_new_action: 0
- notes_zh: 本批次只复用既有 tombstone 与 canonical manifest 证据，确认已退役外部 source 不再作为 active source authority；没有新增外部删除动作。

## 边界

- 不读取旧外部 source 正文。
- 不修改源项目。
- 不生成 owner decision。
- 不提升 active。
- 不写 memory。
