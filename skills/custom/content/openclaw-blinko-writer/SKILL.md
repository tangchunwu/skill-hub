---
name: openclaw-blinko-writer
description: 通过 OpenClaw 服务器写入 Blinko。适用于“发到 Blinko”“写成笔记”“加到待办”“保存一下”“把这段分流成 note/todo/blinko”等场景。优先复用服务器上已跑通的 safe_blinko_skill.sh、safe_blinko_router.sh 和 safe_second_brain.sh。
---

# OpenClaw Blinko Writer

用于复用服务器 `openclaw-main` 上已经稳定运行的 Blinko 写入能力，但把入口整理成本地 skill。

## 适用场景

- 用户要写入 Blinko
- 用户要整理成结构化笔记
- 用户要加到待办
- 用户要把原始内容自动分流到 `blinko / note / todo`

## 强约束

- Blinko 写入属于外发动作，只有用户明确确认后才执行。
- 只能通过服务器上的安全脚本执行，不要直接调用底层私有脚本。
- 不在回复里暴露任何 token 或敏感头。

## 类型映射

- `blinko` -> `type:0`：闪念、原始灵感、低摩擦记录
- `note` -> `type:1`：结构化笔记、复盘、方法论、可复用卡片
- `todo` -> `type:2`：待办、提醒、跟进动作

## 推荐流程

先做健康检查：

```bash
bash ~/.codex/skills/openclaw-blinko-writer/scripts/blinko_via_openclaw_server.sh healthcheck
```

自动分类：

```bash
bash ~/.codex/skills/openclaw-blinko-writer/scripts/blinko_via_openclaw_server.sh classify --content-file /path/to/raw.txt
```

确认后自动分流写入：

```bash
bash ~/.codex/skills/openclaw-blinko-writer/scripts/blinko_via_openclaw_server.sh capture --content-file /path/to/raw.txt --confirmed --mode auto
```

## Second Brain

如果用户明确要写入“二脑/第二大脑”，优先走服务器的：

```bash
bash /root/clawd/scripts/safe_second_brain.sh capture ...
```

本 skill 目前先聚焦 Blinko 主链路；如需把 Second Brain 也本地化，再单独拆 skill。

## 依赖

- 服务器别名：`openclaw-main`
- 本地已安装 ssh skill：
  `~/.codex/skills/ssh-skill/scripts/ssh_execute.py`
  `~/.codex/skills/ssh-skill/scripts/ssh_upload.py`
