# Update Playbook

## 自研 skill 更新

1. 修改 `skills/custom/...`
2. 如需变更名称或入口，同时更新 `registry/skills.yaml`
3. 如需兼容旧入口，更新 `registry/aliases.yaml`
4. 导出到目标工具

## 上游 skill 更新

1. 根据 `registry/skills.yaml` 找到来源
2. 重新拉取上游目录或下载包
3. 对比当前本地版本
4. 如果本地无改造，直接覆盖 `upstream`
5. 如果本地有改造，转入 `patched` 流程

## patched skill 更新

1. 先更新对应 upstream skill
2. 对比 patched 与 upstream 差异
3. 手动合并改动
4. 在 registry 中更新备注
