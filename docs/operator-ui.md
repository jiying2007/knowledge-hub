# Knowledge Hub Operator UI

Operator UI 是 Knowledge Hub 的本地只读人工控制面。它的目标是减少“找命令、翻 JSON、手工拼接下一步”的工作，而不是建立第二套事实源或绕开治理门禁。

## 启动

```bash
tools/knowledge-status.sh --ui
```

默认只监听 `127.0.0.1:8765`。需要换端口时：

```bash
tools/knowledge-status.sh --ui --port 8876
```

只读取 operator projection、不启动 HTTP server：

```bash
tools/knowledge-status.sh --ui --json
```

## 页面内容

单屏页面直接投影现有 canonical 状态：

- control-plane status；
- 项目 structural/source/owner/evidence 覆盖；
- `complete-awaiting-declaration` 等需要人工处理的项目；
- evidence contract 的 missing/invalid fields；
- external closure open gaps；
- terminal closure（本机存在 fresh snapshot 时）；
- `knowledge-status` 给出的下一步动作。

JSON API 为 `GET /api/state`，健康检查为 `GET /healthz`。

## 安全与治理边界

- 只绑定 loopback `127.0.0.1`；
- UI 只实现 GET；POST 返回 HTTP 405；
- 不引入数据库、浏览器端持久化或第二份 readiness 计算；
- project readiness 直接复用 product gate 的 canonical evaluator；
- external closure 直接复用 terminal closure evaluator；
- owner approval、release、promote、retire、registry mutation 等写操作不由 UI 执行。

后续需要交互式写操作时，仍应遵循 `Plan → Diff → Governed PR → CI → Merge`，并对 owner/release 等高风险动作保留显式授权。
