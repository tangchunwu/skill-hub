# Skill Hub

`skill-hub` 是个人 skill 的统一主仓，用来管理、脱敏、同步和回退 Codex / Claude / 其他运行环境里的 skill。

当前已纳管 `351` 个 skill。后续多台电脑不要再手工互相复制 skill，统一从这个仓库拉取，再用脚本同步到本机工具目录。

## 快速开始

### macOS / Linux

```bash
git clone https://github.com/tangchunwu/skill-hub.git
cd skill-hub

# 同步到 Codex
python3 scripts/sync_skills.py --target codex-local --mode copy --force

# 同步到 Claude
python3 scripts/sync_skills.py --target claude-local --mode copy --force
```

### Windows PowerShell

```powershell
git clone https://github.com/tangchunwu/skill-hub.git
cd skill-hub

# 同步到 Codex
python scripts/sync_skills.py --target codex-local --mode copy --force

# 同步到 Claude
python scripts/sync_skills.py --target claude-local --mode copy --force
```

Windows 端如果目标目录和默认配置不同，先修改 `registry/sync-targets.yaml` 里的 `root`，再执行同步。

## 常用命令

查看仓库状态：

```bash
python3 scripts/sync_repo.py status
```

只同步一个 skill：

```bash
python3 scripts/sync_skills.py --target codex-local --mode copy --skill personal-blog-publisher-direct --force
```

同步所有启用目标：

```bash
python3 scripts/sync_skills.py --target all --mode copy --force
```

提交并推送：

```bash
python3 scripts/sync_repo.py commit --message "Update skills" --push
```

扫描疑似密钥：

```bash
python3 scripts/scan_skill_secrets.py --path skills/custom/content
```

## 当前结构

```text
skill-hub/
├── registry/
│   ├── skills.yaml        # skill 主登记表
│   ├── aliases.yaml       # 人话别名到 canonical id 的映射
│   └── sync-targets.yaml  # 本机同步目标
├── skills/
│   ├── custom/            # 自研或本地维护 skill
│   ├── upstream/          # 外部原样拉取 skill
│   └── patched/           # 基于上游改造的 skill
├── scripts/               # 同步、扫描、更新、回退脚本
├── docs/                  # 治理规则、库存、更新手册
├── workflows/
└── exports/
```

## 分类概览

当前 registry 分类数量：

| 分类 | 数量 |
| --- | ---: |
| business-ops | 64 |
| engineering | 60 |
| source-command | 48 |
| content | 41 |
| ai-agent | 38 |
| agent-ops | 19 |
| management | 13 |
| product | 11 |
| industry | 10 |
| research | 8 |
| infra | 8 |
| design | 7 |
| media | 6 |
| review | 4 |
| workflow | 4 |
| security | 2 |
| strategy | 2 |
| growth | 2 |
| data | 2 |
| app / image | 1 / 1 |

完整清单见 `docs/current-inventory.md`，真实可导出的来源以 `registry/skills.yaml` 为准。

## 日常工作流

### 修改已有 skill

1. 在 `skills/custom/...` 中修改。
2. 如名称、分类或导出路径变化，更新 `registry/skills.yaml`。
3. 如入口别名变化，更新 `registry/aliases.yaml`。
4. 执行密钥扫描。
5. 同步到本机目标目录验证。
6. 提交并推送。

```bash
python3 scripts/scan_skill_secrets.py --path skills/custom/<category>/<skill>
python3 scripts/sync_skills.py --target codex-local --mode copy --skill <skill> --force
python3 scripts/sync_repo.py commit --message "Update <skill>" --push
```

### 纳管新的本地 skill

1. 先扫描原始目录。
2. 发现 token、API key、password、private key 时，先脱敏。
3. 复制到合适的 `skills/custom/<category>/`。
4. 追加 `registry/skills.yaml`。
5. 必要时追加 `registry/aliases.yaml`。
6. 再扫描仓库副本并同步抽样验证。

```bash
python3 scripts/scan_skill_secrets.py --path ~/.codex/skills/example-skill
```

### 更新上游 skill

```bash
python3 scripts/update_upstream_skills.py --skill create-prd
python3 scripts/update_upstream_skills.py --all --dry-run
```

上游 skill 尽量放在 `skills/upstream/`，如果需要长期私有改造，复制到 `skills/patched/` 并在 registry 里记录原因。

## 安全规则

- 不把 token、API key、password、private key 写入仓库。
- 需要鉴权的 skill 使用环境变量、系统凭据或本机配置文件。
- 用户给出的密钥只用于当前机器验证，不写进 `SKILL.md`、脚本、示例 JSON 或文档。
- 纳管前和提交前都要跑 `scripts/scan_skill_secrets.py`。
- 嵌套 `.git` 目录不能进入仓库；skill 必须以普通文件纳管，不能变成 gitlink。

已知安全例外和处理记录见 `docs/security-exceptions.md`。

## 同步目标

默认同步目标在 `registry/sync-targets.yaml`：

- `codex-local` -> `~/.codex/skills`
- `claude-local` -> `~/.claude/skills`
- `web-runtime` -> `exports/web`，默认关闭

如果在 Windows 上路径不同，可以把 `root` 改成 Windows 路径，例如：

```yaml
root: C:/Users/<YourName>/.codex/skills
```

## 回退

目录级回退由同步脚本自动备份：

- `sync_skills.py --force`
- `update_upstream_skills.py`

仓库级回退使用 rollback commit，不直接重写历史：

```bash
python3 scripts/sync_repo.py rollback --to <commit> --push
```

## 维护原则

- `skill-hub` 是唯一可信源。
- 不长期手改 `~/.codex/skills` 或 `~/.claude/skills`。
- registry 追加尽量保持可审查，不随意重排大文件。
- 每次大批量纳管按分类分批提交。
- 改动后先本机同步验证，再推送到远端。
