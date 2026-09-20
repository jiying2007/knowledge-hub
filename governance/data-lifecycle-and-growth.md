# 长期数据生命周期与增长策略

## 目标

Knowledge Hub 是长期资产，不能只保证“今天可运行”，还要保证多年后仍可验证、可迁移、可恢复、可理解。

## 数据增长预算

机器预算位于 `registry/engineering-budgets.json#data_growth`。

每个 append-only ledger 同时具有：

- `segment_at_bytes`：达到后进入分片候选，不自动删除历史；
- `hard_max_bytes`：超过即视为工程回归，必须分片或归档。

默认策略是 **segment-before-hard-cap**，不是“无限追加直到 Git 变慢”。

## Ledger 分片终态

长期建议：

```text
registry/ledger/<ledger>/
  epoch-0001.jsonl
  epoch-0002.jsonl
  ...
```

每个 epoch 保留：

- previous epoch digest；
- current epoch digest；
- first/last sequence；
- source revision；
- record count。

分片只改变存储布局，不改变 canonical 语义；旧 epoch 保持 immutable。

## Durable Evidence

GitHub Actions artifact 是短期 payload，不作为多年后的唯一证明。

长期证据分成两层：

```text
ephemeral payload
  logs / reports / workflow artifacts
        ↓ may expire

durable identity
  source SHA
  run / attestation identity
  content digest
  signer workflow
  root/immediate source provenance
  evidence refs
        ↓ retained in bounded ledger
```

`registry/durable-evidence-ledger.jsonl` 只保存有界身份、digest 和可追溯引用，不保存大日志、raw prompt 或设备敏感正文。

## Evidence record 触发条件

只在有长期意义的事件记录 durable row：

- hosting posture ratchet；
- provider evidence binding ratchet；
- strict real external evidence ratchet；
- terminal closure；
- release qualification；
- breaking contract migration。

普通 CI 成功不逐次写入 tracked ledger，避免自触发 commit loop。

## 恢复

恢复必须同时考虑：

1. Git canonical content；
2. registry / ledger；
3. immutable artifact references；
4. hosted repository posture；
5. external evidence refs。

derived index/cache/telemetry 丢失后应可安全重建。
