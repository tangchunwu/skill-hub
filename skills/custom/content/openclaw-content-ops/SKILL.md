---
name: openclaw-content-ops
description: 基于 OpenClaw 服务器的内容运营技能组。适用于“上传图片拿外链”“整理并发布到个人博客”“写入 Blinko/待办/结构化笔记”等一整套内容处理场景。优先复用已整理好的 openclaw-image-bed-uploader、openclaw-personal-blog-publisher、openclaw-blinko-writer 三个子能力。
---

# OpenClaw Content Ops

这是一个内容运营总入口 skill，用于统一调度三条已经整理好的能力：

- 图床上传
- 个人博客整理与发布
- Blinko 写入 / 自动分流

## 什么时候用

- 需要先把图片上传到图床，再拿 URL 给博客或笔记用
- 需要把一段原始内容整理成博客 JSON
- 需要把内容发到个人博客
- 需要把内容写入 Blinko，或者自动分流成 `blinko / note / todo`

## 调用顺序建议

### 1. 只有图片

直接走图床上传：

```bash
bash ~/.codex/skills/openclaw-image-bed-uploader/scripts/upload_via_openclaw_server.sh upload --file /path/to/image.jpg
```

### 2. 只有文字，要发博客

先整理成博客 JSON；确认后再发布：

```bash
bash ~/.codex/skills/openclaw-personal-blog-publisher/scripts/publish_via_openclaw_server.sh --json-file /path/to/blog.json
```

### 3. 只有文字，要发 Blinko

先分类；确认后再 capture：

```bash
bash ~/.codex/skills/openclaw-blinko-writer/scripts/blinko_via_openclaw_server.sh classify --content-file /path/to/raw.txt
bash ~/.codex/skills/openclaw-blinko-writer/scripts/blinko_via_openclaw_server.sh capture --content-file /path/to/raw.txt --confirmed --mode auto
```

### 4. 图片 + 博客

推荐顺序：
1. 图床上传拿 URL
2. 把 URL 填进博客 JSON 的 `coverUrl` 或 `imageUrls`
3. 确认后发布

### 5. 图片 + Blinko

推荐顺序：
1. 图床上传拿 URL
2. 把 URL 附到原始内容里
3. 走 Blinko classify / capture

## 强约束

- 博客发布和 Blinko 写入都属于外发动作，必须明确确认。
- 图床上传只返回 URL，不默认继续发消息或写博客。
- 统一复用下列 skill，不在这个总 skill 里重复实现：
  - `openclaw-image-bed-uploader`
  - `openclaw-personal-blog-publisher`
  - `openclaw-blinko-writer`

## 子能力位置

Codex:
- `~/.codex/skills/openclaw-image-bed-uploader`
- `~/.codex/skills/openclaw-personal-blog-publisher`
- `~/.codex/skills/openclaw-blinko-writer`

Claude Code:
- `~/.claude/skills/openclaw-image-bed-uploader`
- `~/.claude/skills/openclaw-personal-blog-publisher`
- `~/.claude/skills/openclaw-blinko-writer`
