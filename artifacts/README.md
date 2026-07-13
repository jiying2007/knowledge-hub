# Artifacts

# Artifacts

本目录保存非正文制品的结构化证据和受控附件副本。

- `manifests/`：artifact-ref、owner gate、验证、审计和终态证据；不等同于 `registry/items.jsonl`。
- `vault/`：仅保存经批准、体量受控、不可变且有逐文件 `size`/`sha256` 清单的附件副本。缺失、hash/size 漂移或无清单额外文件由 `knowledge-check` 阻断。

raw log、core、SDK、release binary、源码包和运行时 secret 不得进入 vault。清单中标为 `external-reference-only` 的对象只保留 URI/size/hash provenance，不得声称本地文件存在。

Do not store raw SDK packages, logs, core dumps, release binaries, credentials, private keys, tokens, cookies, or other secrets here.
