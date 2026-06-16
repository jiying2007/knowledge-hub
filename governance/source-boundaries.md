# Source Boundaries

## Source Types

| Source | Role | Authority |
| --- | --- | --- |
| `~/embedded/knowledge` | 团队旧知识库 | team-knowledge source |
| `~/embedded/engineering_archive` | 工程旧归档 | project-history source |
| `~/embedded/patent_disclosure` | 专利旧材料 | patent source |
| `~/codex/docs/archive` | Codex 旧归档 | codex-governance source |
| `~/.codex/memories` | Codex 生成记忆 | auxiliary recall only |
| 项目仓 docs | 项目旧文档 | project-current source |

## Boundary Decisions

- team knowledge 不接收项目 lifecycle 目录正文。
- engineering archive 不保存当前项目活文档正文。
- project current 不保存跨项目标准。
- patent domain 不保存通用工程 runbook。
- codex domain 不保存工程事实正文。
- memories 不作为唯一 source。
