# pcr02-project-root-artifacts

## 定位

- Source ID: `pcr02-project-root-artifacts`
- Hub source path: `sources/pcr02-project-root-artifacts`
- Role: `hub-migrated-source`
- Authority: `knowledge-hub-canonical`
- Final disposition: `hard-migrated-to-hub`
- Migration strategy: `hard-migrated-to-hub-project-root-shallow`
- Owner: `pcr02-registry-owner`
- Review after: `2026-09-20`

## Hub 管理方式

pcr02-project-root-artifacts 的旧浅层正文副本已按终态剪枝；项目根目录不再作为知识 source path，仅保留 hash/provenance。

## 边界

- `path` 指向 Hub 内 source 控制目录；当前知识入口只使用 Hub 内路径。
- Hub 统一管理 source 的清单、覆盖状态、当前策略和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料不得作为 active source 入口。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active，不重新回源读取作为默认路径。

## 当前风险

root loose artifact、日志、patch、脚本和生成物不得被复制为 Hub 正文。

## 维护入口

- 清单：`sources/pcr02-project-root-artifacts/inventory.jsonl`
- 覆盖：`sources/pcr02-project-root-artifacts/coverage.md`
- 策略：`sources/pcr02-project-root-artifacts/source-policy.md`
