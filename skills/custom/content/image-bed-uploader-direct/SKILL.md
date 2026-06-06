---
name: image-bed-uploader-direct
description: 通过 openclaw-tu 图床 API 直连上传本地图片并返回外链。适用于“上传图片到图床”“拿图片外链”“不用 SSH 上传图床”“给博客准备 coverUrl 或 imageUrls”等场景。
---

# Image Bed Uploader Direct

用于直连 `openclaw-tu` 图床接口，不经过 `openclaw-main` 或 SSH。

## 适用场景

- 上传本地图片到图床
- 获取公网图片 URL
- 给博客 JSON 的 `coverUrl`、`imageUrls` 准备图片链接

## 强约束

- 不把 token 写入 `SKILL.md` 或输出内容。
- 只做图片上传和 URL 返回，不默认发布博客。
- 成功后优先返回可直接访问的完整 URL。

## 环境变量

必需：

```bash
IMGBED_TOKEN="你的图床 Bearer Token"
```

可选：

```bash
IMGBED_BASE_URL="https://openclaw-tu.us.ci"
IMGBED_UPLOAD_URL="https://openclaw-tu.us.ci/upload"
IMGBED_FIELD_NAME="file"
```

说明：已验证 `Authorization: Bearer $IMGBED_TOKEN` 加 `file=@图片路径` 可以上传成功。上传密码如果只用于网页登录，不需要写入本 skill。

## 使用入口

健康检查：

```bash
python ~/.codex/skills/image-bed-uploader-direct/scripts/upload_image_direct.py healthcheck
```

上传图片：

```bash
python ~/.codex/skills/image-bed-uploader-direct/scripts/upload_image_direct.py upload --file /path/to/image.jpg
```

脚本会解析接口返回里的 `src`、`url` 或 `href` 字段；如果返回相对路径，会自动拼接 `IMGBED_BASE_URL`。
