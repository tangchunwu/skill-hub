# Security Exceptions

## baoyu-danger-x-to-markdown

- 状态：用户确认允许纳管。
- 风险：`scripts/cookies.ts` 中存在日志输出 `auth_token` 前缀的代码。
- 处理：当前不写入硬编码 token；后续建议改成默认不打印 cookie token 前缀。

## source-command-kotlin-test

- 状态：暂缓纳管。
- 风险：`SKILL.md` 示例中包含 `SecureP@ss1` 形式的密码样例。
- 处理：后续将示例改成 `<PASSWORD>` 或环境变量占位后再纳管。

