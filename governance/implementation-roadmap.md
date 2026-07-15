# Knowledge Hub 实施历史记录（已完成）

> 本页只记录初始建设阶段的完成范围，不是当前 roadmap、待办列表或新增入口。当前产品状态以 `governance/product/validation/project-readiness.md` 和实时 product gate 输出为准。

## 已完成范围

- 建立 canonical 目录、registry、source control、索引、模板与治理文档。
- 建立 check、search、context、capture、生命周期、回归、恢复和 product gate 工具链。
- 将项目知识入口收敛到 `projects/<project>/current|decisions|validation|archive`。
- 将团队通用知识收敛到 `domains/`，将普通与个人笔记收敛到 `notes/`。
- 将 source 主表限定为仍参与当前默认入口的 registered source；历史 source 只在 provenance ledger 中审计。
- 将 Codex 自动化限定为声明式、report-only 或显式授权执行。

## 当前维护入口

```bash
rtk bash ~/knowledge-hub/tools/knowledge-health-summary.sh --json
rtk bash ~/knowledge-hub/tools/knowledge-check.sh --dry-run --json --diagnostics
rtk bash ~/knowledge-hub/tools/knowledge-final-gate.sh --json --final-profile product
```

新的功能或治理变化必须形成独立需求、证据和验收，不在本历史记录中追加 Phase。
