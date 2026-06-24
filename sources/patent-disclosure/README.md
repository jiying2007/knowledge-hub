# patent-disclosure

## 定位

- Source ID: `patent-disclosure`
- Source path: `~/embedded/patent_disclosure`
- Role: `patent-source`
- Authority: `patent-materials`
- Final disposition: `mixed-terminal-coverage`
- Migration strategy: `patent-copy-first-plus-artifact-ref`
- Owner: `leiwenjun`
- Review after: `2026-09-20`

## Hub 管理方式

Patent disclosure Markdown 与附件引用已进入 Hub 治理。

## 边界

- Hub 统一管理的是 source 的清单、覆盖状态、可读摘要、证据和可复用提取物。
- raw session、history、源码树、大文件、二进制、压缩包、PDF、日志和敏感材料默认不复制正文。
- 需要进入 `projects/`、`domains/` 或 `notes/` 的长期正文，必须由 registry、migration、owner gate 或 evidence refs 支撑。
- 不修改源项目，不写 `~/.codex/memories`，不自动提升 active。

## 当前风险

专利语义和法律状态仍需 owner/legal review。

## 维护入口

- 清单：`sources/patent-disclosure/inventory.jsonl`
- 覆盖：`sources/patent-disclosure/coverage.md`
- 计划：`sources/patent-disclosure/migration-plan.md`
