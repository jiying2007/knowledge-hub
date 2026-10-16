# LAN Team MCP 客户端接入与验收

适用范围：Knowledge Hub v1.3 团队只读 Profile。这个 Profile 使用本仓的 MCP
2026-07-28 Native 协议，**必须用工程师的真实 Codex CLI/VS Code 版本验证**。
官方 conformance 通过不证明客户端自动兼容。本页示例是安装模板，不是已部署的地址。

## 统一入口（只选一种）

- 局域网 HTTPS：`https://knowledge.example.internal/mcp`；内网 DNS、TLS 信任链和 Caddy
  的 Host/Origin、来源网段均需经真实设备检查。
- SSH 试点：先在**使用该客户端的同一台机器**开启
  `ssh -N -L 3000:127.0.0.1:3000 <user>@<internal-server>`，
  然后使用 `http://127.0.0.1:3000/mcp`。
  隧道只有 localhost 监听端口映射，不得使用 `-g` 开给整个网络。

两种入口都必须传只读共享 Bearer；不向 GitHub、项目文件或聊天正文写令牌。
成员只要知道团队 MCP URL 和经内部渠道发放的令牌，不需要完整克隆 Hub 才能读知识。

## Codex CLI（Linux / Windows SSH Ubuntu）

配置用户级 `~/.codex/config.toml`（CLI 和 Codex IDE 共用）：

```toml
[mcp_servers.knowledge_hub]
url = "http://127.0.0.1:3000/mcp"
bearer_token_env_var = "KNOWLEDGE_HUB_TEAM_TOKEN"
```

使用内网 HTTPS 时将 url 替换为经过验证的 HTTPS URL。通过个人本地受限文件提供
令牌，而不将令牌字面值写入配置或 Git：

```bash
install -d -m 700 ~/.config/knowledge-hub
# 用受信方式将只读团队令牌保存到该目录下的 team-token 文件，chmod 600。
export KNOWLEDGE_HUB_TEAM_TOKEN="$(cat ~/.config/knowledge-hub/team-token)"
codex --version
codex mcp list
```

在 Codex 中实际调用 knowledge_search / knowledge_get / knowledge_context，
检查 source_path、serving_sha、review_required 是否正确。离开会话时清理环境变量
`unset KNOWLEDGE_HUB_TEAM_TOKEN`；令牌轮换后重新配置。环境变量仍可能被同用户代码读取，
所以令牌应严格只读、定期轮换，并避免在不可信工作区运行代码。

## VS Code（使用用户配置，不提交令牌）

执行 `MCP: Open User Configuration`，在个人用户的 mcp.json 中配置：

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "khTeamToken",
      "description": "Knowledge Hub team read-only token",
      "password": true
    }
  ],
  "servers": {
    "knowledge_hub": {
      "type": "http",
      "url": "https://knowledge.example.internal/mcp",
      "headers": {
        "Authorization": "Bearer ${input:khTeamToken}"
      }
    }
  }
}
```

个人 VS Code 配置允许 `inputs` 密码输入；不应把该变量放在通用可共享
`.mcp.json` 的 portable 配置里，因为不同宿主对交互式输入的支持不同。
开启 VS Code 的 MCP 工具目录，实际调用上述三个工具。若是 Windows 上的
VS Code 但 MCP 服务在 Ubuntu SSH 隧道另一端，必须确认隧道运行在哪台机器、
以及相应环境的 localhost 指向什么位置。

## 最小现场验收证据（两位成员分别执行）

1. 记录真实 Codex CLI 版本、VS Code 版本与使用的接入方式，不复制令牌。
2. 无令牌、错误令牌、错误 Origin/Host 必须拒绝；正确凭证可调用三个只读工具。
3. 中文 FOC / UBIFS / SSC305 查询命中可追溯，get 读取的正文与 search 的 id 匹配。
4. Draft、Personal、Rejected、Archived 与私有路径在三条工具链中均不可见。
5. 两位工程师各自运行一次真实 Git PR 提交或更新；PR CI 和发布 SHA 可追溯。
6. 服务器断开 GitHub、索引损坏和候选发布失败后仍可查询上一已验证版本。

如果协议或环境不兼容，保留 **具体客户端版本 + request/response 错误码 +
服务器版本 SHA**，禁止通过放开无凭证端口、关闭 TLS 或跳过只读边界凑成功。

官方客户端参考：OpenAI Codex MCP 配置与 VS Code MCP 配置文档
（按使用时最新实际版本校验）。
