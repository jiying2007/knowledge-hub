# sdk-upgrade-risk-review

## 触发词

- SDK 升级
- BSP 升级风险
- ABI 兼容检查
- 工具链或 rootfs 升级

## 工作流

1. 建立升级前基线。
2. 分层审查替换面。
3. 审计依赖和回归范围。
4. 输出回滚策略。

## 验证

```bash
rtk bash scripts/check-all.sh
```
