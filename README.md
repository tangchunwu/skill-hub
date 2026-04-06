# Skill Hub

统一管理自研 skill、上游 skill、工作流、同步目标和版本回退的总仓。

这个仓库解决的是 skill 生命周期管理，而不只是“把 skill 放在哪”：

- 自己写的 skill 如何长期维护
- 外部拉取的 skill 如何跟踪上游更新
- Skill 如何同步到 Codex / Claude / Web
- Skill 改坏以后如何回退
- 多台电脑、多工具之间如何保持一致

## 核心目标

- 单一可信源：只认 `skill-hub` 为主仓
- 来源可追踪：每个 skill 都记录来源和路径
- 命名可统一：别名和主名称分离管理
- 分发可控：导出到不同工具时不再手工复制
- 回退安全：支持目录级备份和仓库级 rollback commit

## 当前纳管的 skill

### Product / Research

- `create-prd`
- `competitor-analysis`
- `tavily-research`
- `summarize-interview`
- `prioritization-frameworks`
- `customer-journey-map`

### Strategy / Growth / Management

- `okr-coach`
- `executive-update-generator`
- `go-to-market-strategy`
- `ab-test-analysis`
- `altitude-horizon-framework`

### Custom / Ops / Content

- `flow2api-imagegen`
- `minecontext-sync-soul-mirror`
- `openclaw-blinko-writer`
- `openclaw-content-ops`
- `openclaw-image-bed-uploader`
- `openclaw-personal-blog-publisher`
- `qclaw-asar-hotfix`
- `ssh-skill`

## 目录结构

```text
skill-hub/
├── registry/
│   ├── skills.yaml
│   ├── aliases.yaml
│   └── sync-targets.yaml
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

### `skills/custom/`

你自己编写和长期维护的 skill。

特点：

- 你是唯一维护者
- 名称和结构由你定义
- 变更直接进入 Git 历史

### `skills/upstream/`

从外部来源原样拉取的 skill。

特点：

- 尽量不直接改
- 保留真实上游名称
- 定期重新同步

### `skills/patched/`

基于上游 skill 做过本地改造的版本。

特点：

- 必须在 registry 记录来源
- 必须记录为何不能只用 upstream
- 上游更新时需要人工合并

## Registry 规则

### `registry/skills.yaml`

记录每个 skill 的：

- canonical name
- 类型
- 来源
- 本地路径
- 是否允许导出
- 适用工具
- 更新策略

### `registry/aliases.yaml`

记录：

- 人话入口
- 历史旧名
- 业务别名

这些别名统一映射到主 skill 名。

### `registry/sync-targets.yaml`

记录：

- 同步目标
- 目标根目录
- 导出模式
- 是否启用

## 脚本

当前提供 3 个基础脚本：

### `scripts/update_upstream_skills.py`

作用：

- 按 registry 中记录的来源重新拉取上游 skill
- 支持 GitHub 路径型和直接下载 zip
- 更新前自动备份现有目录

示例：

```bash
python3 scripts/update_upstream_skills.py --all
python3 scripts/update_upstream_skills.py --skill create-prd
python3 scripts/update_upstream_skills.py --all --dry-run
```

### `scripts/sync_skills.py`

作用：

- 将 skill-hub 中允许导出的 skill 同步到目标工具目录
- 支持 `copy` 和 `symlink`
- 支持批量同步所有启用目标

示例：

```bash
python3 scripts/sync_skills.py --target codex-local --mode symlink --force
python3 scripts/sync_skills.py --target claude-local --mode symlink --force
python3 scripts/sync_skills.py --target all --mode symlink --force
```

### `scripts/sync_repo.py`

作用：

- 查看仓库状态
- 提交并推送改动
- 安全回退到指定提交内容

示例：

```bash
python3 scripts/sync_repo.py status
python3 scripts/sync_repo.py commit --message "Update skills" --push
python3 scripts/sync_repo.py rollback --to <commit> --push
```

## 回退机制

### 1. 目录级回退

以下操作在覆盖前会自动备份原目录：

- `update_upstream_skills.py`
- `sync_skills.py --force`

适合：

- 单个 skill 被错误覆盖
- 导出目录被不稳定内容污染

### 2. 仓库级回退

`sync_repo.py rollback` 不会直接重写历史，而是：

1. 将工作树恢复到指定提交内容
2. 生成一个新的 rollback commit
3. 可选择推送到远端

这样更适合 Agent 场景，避免误用危险命令。

## 推荐工作流

### 自研 skill 更新

1. 修改 `skills/custom/...`
2. 更新 `registry/skills.yaml`
3. 如需兼容旧入口，更新 `registry/aliases.yaml`
4. 运行 `sync_skills.py`
5. 运行 `sync_repo.py commit --push`

### 上游 skill 更新

1. 运行 `update_upstream_skills.py`
2. 检查变更
3. 运行 `sync_skills.py --target all`
4. 运行 `sync_repo.py commit --push`

### 紧急回退

1. 用 `sync_repo.py status` 查看当前状态
2. 找到要回退到的 commit
3. 执行 `sync_repo.py rollback --to <commit> --push`

## 设计约束

- 不直接把 `~/.codex/skills` 或 `~/.claude/skills` 当主仓
- 不在导出目录长期手改 skill
- 不在 `upstream` 目录里直接做长期私有修改
- 一切变更先回到 `skill-hub`

## 下一步

后续建议继续补：

- `ingest_local_changes.py`
  - 把工具目录中的临时修改回收到 `skill-hub`

- `build-exports`
  - 为 Web 产品生成运行时导出结果

- `patched` skill 的自动差异检查
