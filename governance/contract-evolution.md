# Contract Evolution

## 原则

Knowledge Hub 继续坚持 strict-current-contract：

- breaking change 使用新 contract id；
- runtime 默认不保留长期 shim；
- unknown version fail closed。

为了避免跨仓 consumer 被同步升级绑死，新增 `registry/contract-compatibility.json` 管理升级过程。

## Breaking change 流程

```text
new contract id
  ↓
migration manifest
  ↓
consumer declaration/discovery
  ↓
compatibility evidence
  ↓
producer switch
  ↓
old contract retirement
```

consumer declaration 只记录已验证事实；未知 consumer 不推断支持范围。

## AI-first

AI 可自动：

- 搜索 known repository refs 中的 consumer contract；
- 生成 compatibility candidate；
- 生成 migration diff；
- 运行 consumer CI；
- 创建 governed PR。

人工只在 breaking semantics、owner exception 或无法自动验证的外部 consumer 上介入。
