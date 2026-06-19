# Knowledge Hub manual entry owner override 2026-06-19

## 结论

`knowledge-new.sh` 现在支持 `--owner <owner>`，人工新增条目时可以直接在 registry 草稿中指定真实 owner。默认 owner 仍是 `leiwenjun`，保持现有用法兼容。

这个修复减少把所有新增知识默认压到单一 owner 的维护瓶颈；它只影响只读草稿，不自动写 registry。

## 问题地图

| ID | 问题 | 风险 | 处理 |
|---|---|---|---|
| MOO-001 | `knowledge-new.sh` 的 registry 草稿固定输出 `owner=leiwenjun`。 | 人工新增团队或项目条目时容易忘记改 owner，导致长期维护集中到一个人。 | 增加 `--owner <owner>` 参数。 |
| MOO-002 | 默认行为不能破坏已有使用方式。 | 现有命令如果必须新增 owner 参数，会增加维护负担。 | 默认 owner 仍为 `leiwenjun`。 |
| MOO-003 | owner 覆盖需要可回归。 | 后续改动可能重新硬编码 owner。 | 新增 `manual-entry-owner-override` 回归场景。 |

## 决策

- `--owner` 只影响输出草稿，不写入仓库。
- 不在 `knowledge-new.sh` 中校验 owner registry，避免只读向导变重；最终仍由 `knowledge-check` 的 owner registry gate 校验已落盘条目。
- 保持默认 `leiwenjun`，减少兼容成本。

## Evidence Index

| Command | Exit Code | Result Summary | Evidence Path | Layer | Related Artifact |
|---|---:|---|---|---|---|
| `rtk bash tools/knowledge-new.sh --kind decision --domain governance --id governance-owner-default --path governance/owner-default.md` | 0 | 通过；未传 `--owner` 时 registry 草稿默认 `owner=leiwenjun` | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-owner-override-20260619` |
| `rtk bash tools/knowledge-new.sh --kind decision --domain governance --owner team-core --id governance-owner-override --path governance/owner-override.md` | 0 | 通过；传入 `--owner team-core` 时 registry 草稿输出 `owner=team-core` | `tools/knowledge-new.sh` | Tool | `knowledge-hub-manual-entry-owner-override-20260619` |
| `rtk bash tools/knowledge-regression.sh --json` | 0 | 通过；11 个回归场景全部 pass，包含新增 `manual-entry-owner-override` 场景 | `tools/knowledge-regression.sh` | Tool | `knowledge-hub-manual-entry-owner-override-20260619` |
| `rtk bash tools/knowledge-check.sh --dry-run --json --diagnostics` | 0 | 通过；0 errors、0 warnings，确认新增 manifest、registry 和 index 登记无漂移 | `tools/knowledge-check.sh` | Tool | `knowledge-hub-manual-entry-owner-override-20260619` |

## 边界

- 不自动创建正文、registry、migration 或 index。
- 不绕过 owner registry gate；真实落盘后仍由 `knowledge-check` 校验 owner。
- 不修改 PCR02 源项目 docs。
- 不关闭 owner gate，不生成 owner decision。
- 不启用自动化，不写 memory。
