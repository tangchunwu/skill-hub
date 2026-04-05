# Scripts

当前已提供 3 个基础脚本：

- `sync_skills.py`
  - 将 `skill-hub` 中登记且允许导出的 skill 同步到 Codex / Claude
  - 支持 `copy` 和 `symlink`
  - `--force` 时会先做目录备份

- `update_upstream_skills.py`
  - 按 registry 中记录的来源重新拉取上游 skill
  - 支持 GitHub 仓库路径和直接下载 zip
  - 更新前会对现有目录做备份

- `sync_repo.py`
  - 统一执行仓库状态查看、提交推送和回退
  - 回退采用“生成新的 rollback commit”，不直接改写历史

## 推荐用法

```bash
python3 scripts/update_upstream_skills.py --all
python3 scripts/sync_skills.py --target codex-local --mode symlink --force
python3 scripts/sync_skills.py --target all --mode symlink --force
python3 scripts/sync_repo.py commit --message "Update upstream skills" --push
python3 scripts/sync_repo.py rollback --to <commit> --push
```

## 关于 `--target all`

- `--target all` 会遍历 `registry/sync-targets.yaml` 中所有 `enabled: true` 的目标
- 适合在同一次修改后同时同步到 Codex 和 Claude
- 如果某个 skill 在某个目标已存在且未加 `--force`，会显示 `skip_exists`

## 回退策略

- skill 目录级回退：由 `sync_skills.py` 和 `update_upstream_skills.py` 在覆盖前创建备份
- 仓库级回退：由 `sync_repo.py rollback` 生成新的回退提交
