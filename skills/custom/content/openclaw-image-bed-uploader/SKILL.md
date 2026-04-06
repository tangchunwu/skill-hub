---
name: openclaw-image-bed-uploader
description: 通过 OpenClaw 服务器把本地图片上传到现有图床并返回可访问 URL。适用于“上传这张图到图床”“给我一个外链”“把图片发到 openclaw-tu 图床”等场景。优先复用服务器上已经跑通的上传接口和鉴权，不在本地暴露敏感配置。
---

# OpenClaw Image Bed Uploader

用于复用服务器 `openclaw-main` 上已经稳定可用的图床上传能力。

## 适用场景

- 上传本地图片到图床
- 获取图片外链
- 给博客、Blinko、消息发送准备公网图片 URL

## 强约束

- 不在本地 skill 中硬编码图床 token。
- 上传动作走服务器现有配置与脚本约定。
- 只做图片上传与 URL 返回，不默认做消息发送。

## 推荐入口

健康检查：

```bash
bash ~/.codex/skills/openclaw-image-bed-uploader/scripts/upload_via_openclaw_server.sh healthcheck
```

上传图片：

```bash
bash ~/.codex/skills/openclaw-image-bed-uploader/scripts/upload_via_openclaw_server.sh upload --file /path/to/image.jpg
```

成功时输出图片 URL。

## 依赖

- 服务器别名：`openclaw-main`
- 本地已安装 ssh skill：
  `~/.codex/skills/ssh-skill/scripts/ssh_execute.py`
  `~/.codex/skills/ssh-skill/scripts/ssh_upload.py`

## 服务器侧已知来源

图床能力来自服务器上的现有链路，例如：
- `scripts/test_morning_brief_upload.sh`
- `scripts/telegram_image_mvp.sh`
- `scripts/image_pipeline.sh`

本 skill 只调用服务器现有上传能力，不自行维护接口密钥。
