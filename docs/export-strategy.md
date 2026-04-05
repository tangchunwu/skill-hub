# Export Strategy

## 导出目标

- Codex
- Claude
- Web 产品

## 推荐方式

### Codex / Claude

- 优先软链接
- 如果目标工具不稳定支持软链接，再改为复制

### Web 产品

- 不直接复用原目录
- 通过构建脚本筛选需要的 skill
- 输出到 `exports/web/`

## 导出原则

- 只导出 `registry/skills.yaml` 中 `exported: true` 的 skill
- 别名由运行时路由处理，不直接复制成多个目录
