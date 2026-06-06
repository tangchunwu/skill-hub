---
name: content-ops-direct
description: 直连内容运营组合技能。适用于“先上传图片再发个人博客”“图片配合博客 JSON”“不用 SSH 做图床和个人博客发布”“整理内容并发布到 mianhua.me”等场景。优先复用 image-bed-uploader-direct 和 personal-blog-publisher-direct。
---

# Content Ops Direct

用于把直连图床和直连个人博客发布串起来，不经过 `openclaw-main` 或 SSH。

## 子能力

- 图床上传：`image-bed-uploader-direct`
- 个人博客发布：`personal-blog-publisher-direct`

## 推荐流程

### 只有文字，要发博客

1. 先按 `personal-blog-publisher-direct` 整理成单个博客 JSON。
2. 用户明确确认后，调用：

```bash
python ~/.codex/skills/personal-blog-publisher-direct/scripts/publish_blog_direct.py --json-file /path/to/blog.json
```

### 图片 + 博客

1. 先用 `image-bed-uploader-direct` 上传图片：

```bash
python ~/.codex/skills/image-bed-uploader-direct/scripts/upload_image_direct.py upload --file /path/to/image.jpg
```

2. 把返回 URL 填入博客 JSON：

- 主图填 `coverUrl`
- 正文配图填 `imageUrls`
- Markdown 正文里需要展示时，用 `![](图片URL)`

3. 用户明确确认后，再调用博客发布脚本。

## 环境变量

必需：

```bash
BLOG_UPSERT_TOKEN="你的博客 Bearer Token"
IMGBED_TOKEN="你的图床 Bearer Token"
```

可选：

```bash
BLOG_UPSERT_URL="https://mianhua.me/api/blog/external/upsert"
IMGBED_BASE_URL="https://openclaw-tu.us.ci"
IMGBED_UPLOAD_URL="https://openclaw-tu.us.ci/upload"
IMGBED_FIELD_NAME="file"
```

## 安全约束

- 博客发布属于外发动作，必须明确确认。
- 图床上传只返回 URL，不默认继续发布博客。
- 不把 token 写入 skill 文件、博客 JSON 或最终回复。
