# Update Playbook

## 自研 skill 更新

1. 修改 `skills/custom/...`
2. 如需变更名称或入口，同时更新 `registry/skills.yaml`
3. 如需兼容旧入口，更新 `registry/aliases.yaml`
4. 运行 `scripts/scan_skill_secrets.py` 扫描新增或修改的 skill
5. 导出到目标工具

## 自研 skill 纳管前脱敏

1. 先对候选目录运行扫描：

```bash
python3 scripts/scan_skill_secrets.py --path ~/.codex/skills/example-skill
```

2. 如果发现疑似密钥，优先改成环境变量读取。
3. 再把脱敏后的 skill 复制到 `skills/custom/...`。
4. 更新 registry 和 aliases。
5. 提交前再扫描一次仓库内的目标目录。

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
