# Skill Hub

这是一个用于统一管理自研 skill、上游 skill、工作流和分发目标的总仓。

目标不是把 skill 堆在某个工具目录里，而是让 skill 具备：

- 单一可信源
- 可追踪来源
- 可跨工具分发
- 可跨机器同步
- 可持续更新

## 目录结构

```text
skill-hub/
├── registry/
├── skills/
│   ├── custom/
│   ├── upstream/
│   └── patched/
├── workflows/
├── exports/
├── scripts/
└── docs/
```

## 三类 skill

### custom

你自己编写和长期维护的 skill。

特点：

- 你是唯一维护者
- 版本跟随你的仓库
- 可以自由修改结构和命名

### upstream

从外部原样拉取的 skill。

特点：

- 尽量不直接改
- 保留真实上游名称
- 可定期重新同步

### patched

基于上游 skill 做过本地改造的版本。

特点：

- 必须在 registry 里记录来源和改动原因
- 更新上游时要谨慎合并

## 核心原则

- 所有 skill 都必须登记在 `registry/skills.yaml`
- 所有别名都必须登记在 `registry/aliases.yaml`
- 不允许把工具目录当作主存储
- 不允许直接在导出目录里手改 skill
- 先更新 skill-hub，再导出到 Codex / Claude / Web

## 使用顺序

1. 新增或拉取 skill
2. 更新 registry
3. 更新 aliases
4. 导出到目标工具目录
5. 在具体项目或工作流中使用

## 第一阶段目标

当前只先解决：

- skill 统一存储
- skill 来源可追踪
- skill 命名统一
- 可导出到 Codex / Claude / Web

后续再补：

- 自动同步脚本
- 自动检查上游更新
- 自动构建导出目录
