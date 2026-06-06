---
name: openclaw-channel-bootstrap
description: 为网页应用快速接入 OpenClaw 通道配置，自动输出可直接复制的 Webhook URL 与 Token。用于用户说“帮我配置 OpenClaw 通道”“给我 Webhook 和 Token”“一键生成接入参数”“OpenClaw 对话接入配置”这类场景，支持外部网页与本地网页两种模式，减少手工查配置和复制错误。
---

# OpenClaw Channel Bootstrap

## 目标

执行一次后，直接给用户两项配置值：
1. `Webhook URL`
2. `Token`

## 执行步骤

1. 优先执行脚本（自动模式，优先外部地址）：

```bash
bash skills/openclaw-channel-bootstrap/scripts/emit_channel_config.sh --target auto
```

2. 外部网页（公网/域名）场景，显式指定：

```bash
bash skills/openclaw-channel-bootstrap/scripts/emit_channel_config.sh \
  --target external \
  --public-base "https://ccnu.ccwu.cc"
```

3. 本地网页（同机 localhost）场景，显式指定：

```bash
bash skills/openclaw-channel-bootstrap/scripts/emit_channel_config.sh \
  --target local
```

4. 将脚本输出按固定格式回复给用户，且只返回这两项：

```text
Webhook URL: <value>
Token: <value>
```

5. 额外校验（回复前必须做）：
- `Webhook URL` 必须以 `http://` 或 `https://` 开头
- `Token` 不能为空，且不包含中文全角字符

6. 若脚本报错：
- 外部地址缺失：提示用户传 `--target external --public-base`
- 缺 Token：提示检查 `/root/.config/openclaw/gateway.env` 的 `OPENCLAW_GATEWAY_PASSWORD`
- 配置文件不可读：返回明确文件路径和失败原因，不编造结果

## 输出规范（必须遵守）

- 默认不输出多余解释、步骤、日志。
- 用户明确要求“只给配置值”时，严格只输出两行。
- 不在公开群聊主动暴露 Token；如在群聊触发，先提醒改私聊再给。
