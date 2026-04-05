# Skill Hub 治理规则

## 1. 命名规则

- 上游 skill 保留真实名称
- 自研 skill 用稳定英文 slug
- 不在目录名里使用中文
- 别名统一登记在 `registry/aliases.yaml`

## 2. 来源规则

- 所有外部 skill 必须登记来源
- 外部 skill 默认放到 `skills/upstream/`
- 如果做本地改造，复制到 `skills/patched/`
- 不直接在 `upstream` 目录里长期手改

## 3. 更新规则

- `custom`：直接修改并提交
- `upstream`：重新拉取并对比
- `patched`：先比对上游，再人工合并

## 4. 分发规则

- 不直接把工具目录当主仓
- 一切改动先进入 `skill-hub`
- 再导出到 Codex / Claude / Web

## 5. 清理规则

- 重复命名必须收敛到 canonical name
- 失效 skill 在 registry 中标记，不直接删除历史记录
- 删除 skill 前先确认是否被 workflow 引用
