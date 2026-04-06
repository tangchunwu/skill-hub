---
name: minecontext-sync-soul-mirror
description: Use when the user asks to sync MineContext SQLite data into the Soul Mirror Supabase backend, including key creation, API usage, and validation.
---

# MineContext Sync for Soul Mirror

## Overview

This skill syncs MineContext local SQLite data (daily reports and activities) into Soul Mirror via Supabase edge functions.

## Workflow

1. Confirm target data and account
- Ensure the user wants MineContext sync (not MiniMax).
- Confirm data should map to the logged-in Soul Mirror account only.

2. Verify backend readiness
- Tables: `daily_reports`, `activities`, `minecontext_sync_keys` exist.
- Edge functions deployed:
  - `sync-minecontext` (`verify_jwt = false`)
  - `manage-minecontext-sync-key` (JWT required)

3. Generate sync key in product UI
- Settings -> MineContext 同步 -> “生成新密钥”.
- The key is cached locally until user clears it (not shown again after revoke).

4. Local sync execution
- Configure `.env.sync` with:
  - `SYNC_BASE_URL=https://<project-ref>.supabase.co/functions/v1`
  - `SYNC_API_KEY=<plain sync key>`
  - `MINECONTEXT_DB_PATH=~/Library/Application Support/MineContext/persist/sqlite/app.db`
- Run `python3 scripts/minecontext_sync.py`.

5. Validate results
- SQL checks:
  - `select count(*) from public.daily_reports where user_id = '<USER_ID>';`
  - `select count(*) from public.activities where user_id = '<USER_ID>';`

## Troubleshooting

- `401 Invalid sync key`: key revoked or wrong key; regenerate and retry.
- `inserted=0 updated=0` with non-empty data: confirm `document_type='DailyReport'` and `is_deleted=0` in local DB.
- Edge function errors: check Supabase logs and env secrets.
