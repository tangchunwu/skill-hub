---
name: personal-blog-publisher-direct
description: 通过个人博客外部 upsert API 直连整理并发布博客。适用于“发到我的个人博客”“整理成博客 JSON”“直接调用 mianhua.me 博客接口发布”“不用 SSH 发布博客”等场景。整理阶段只输出单个合法 JSON；只有用户明确确认发布时才调用接口。
---

# Personal Blog Publisher Direct

用于直连个人博客接口，不经过 `openclaw-main` 或 SSH。

## 适用场景

- 把原始草稿、笔记、转发内容整理成博客 JSON
- 直接发布到个人博客
- 用户强调保留原语气、轻编辑、不要 AI 腔

## 强约束

- 默认轻编辑，不重写。
- 尽量保留原表达、原顺序、原判断、原语气。
- 整理阶段只输出单个合法 JSON 对象，不加解释，不包代码块。
- 发布属于外发动作，必须等用户明确确认后才执行，例如 `发布`、`确认执行`、`发过去`。
- 不把 token 写入 `SKILL.md` 或生成的博客 JSON。

## 环境变量

必需：

```bash
BLOG_UPSERT_TOKEN="你的博客 Bearer Token"
```

可选：

```bash
BLOG_UPSERT_URL="https://mianhua.me/api/blog/external/upsert"
```

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
- `slug` 使用英文小写、数字和 `-`。
- 禁止标题党、禁止营销化改写。

接口也支持别名字段：`content/md/body`、`coverUrl/cover`、`imageUrls/images`、`hidden`、`meta`。

## 发布入口

确认发布后，把博客 JSON 保存为文件，再调用：

```bash
python ~/.codex/skills/personal-blog-publisher-direct/scripts/publish_blog_direct.py --json-file /path/to/blog.json
```

脚本会读取 `BLOG_UPSERT_TOKEN`，向 `BLOG_UPSERT_URL` 发起 `POST`，并输出精简回执。
