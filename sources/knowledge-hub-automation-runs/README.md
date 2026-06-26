# knowledge-hub-automation-runs

## 定位

- Source ID: `knowledge-hub-automation-runs`
- Hub source path: `sources/knowledge-hub-automation-runs`
- Role: `hub-native-source`
- Authority: `knowledge-hub-ledger`
- Final disposition: `hub-native-source`
- Source strategy: `hub-native-automation-run-ledger`
- Owner: `leiwenjun`
- Review after: `2026-09-24`

## Hub 管理方式

knowledge-hub-automation-runs 是 Hub 原生账本；source path 收敛为 sources/knowledge-hub-automation-runs，正文权威仍是 registry/automation-runs.jsonl。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

apply-with-review 必须引用授权账本；自动化默认 report-only。

## 维护入口

- 清单：`sources/knowledge-hub-automation-runs/inventory.jsonl`
- 覆盖：`sources/knowledge-hub-automation-runs/coverage.md`
- 策略：`sources/knowledge-hub-automation-runs/source-policy.md`
