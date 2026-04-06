---
name: openclaw-personal-blog-publisher
description: 通过 OpenClaw 服务器整理并发布个人博客。适用于“发到我的个人博客”“整理成博客 JSON”“按我的博客接口发布”“把这段转成可 upsert 的 JSON 并发出去”等场景。先轻编辑整理为单个合法 JSON；只有在用户明确确认发布时，才通过服务器上的现有博客发布能力外发。
---

# OpenClaw Personal Blog Publisher

用于复用服务器 `openclaw-main` 上已经跑通的个人博客工作流，但把入口整理成本地 skill。

## 适用场景

- 用户要把原始草稿、笔记、转发内容整理成博客 JSON
- 用户要发布到个人博客
- 用户强调保留原语气、轻编辑、不要 AI 腔

## 强约束

- 默认是轻编辑，不是重写。
- 尽量保留原表达、原顺序、原判断、原语气。
- 整理阶段只输出单个合法 JSON 对象，不加解释，不包代码块。
- 发布阶段属于外发动作，只有收到明确确认词才执行。

## 输出 JSON 约定

字段：
- `title`
- `slug`
- `content`
- `summary`
- `tags`
- `date`
- `category`
- `coverUrl`
- `imageUrls`
- `meta.hidden`

规则：
- `content` 必须是 Markdown。
- `category` 默认 `notes`。
- `coverUrl` 默认空字符串。
- `imageUrls` 默认空数组。
- `meta.hidden` 默认 `false`。
- `date` 使用北京时间，格式 `YYYY-MM-DDTHH:mm`。

## 生成阶段

当用户只是说“整理成博客 JSON”“给我博客格式”，直接返回单个 JSON 对象。

标题和 slug 规则：
- 标题优先沿用原文核心表达，轻微润色即可。
- slug 使用英文小写和 `-`。
- 禁止标题党、禁止营销化改写。

## 发布阶段

只有用户明确确认后才发布，例如：
- `确认执行`
- `发布`
- `发过去`

发布时不要自己拼远程命令，直接调用本 skill 自带脚本：

```bash
bash ~/.codex/skills/openclaw-personal-blog-publisher/scripts/publish_via_openclaw_server.sh --json-file /path/to/blog.json
```

该脚本会：
1. 上传 JSON 到 `openclaw-main`
2. 在服务器上读取当前生效的博客 skill 配置
3. 用服务器现有凭证执行发布
4. 返回精简回执

## 依赖

- 服务器别名：`openclaw-main`
- 本地已安装 ssh skill：
  `~/.codex/skills/ssh-skill/scripts/ssh_execute.py`
  `~/.codex/skills/ssh-skill/scripts/ssh_upload.py`
