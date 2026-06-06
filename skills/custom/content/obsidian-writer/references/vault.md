# Vault Reference

Default Obsidian vault:

- `/Users/tangchunwu/Documents/Obsidian Vault`

Common folders already used:

- `复盘/`

Recommended folders:

- `复盘/`
- `产品/`
- `技术/`
- `待办/`
- `Daily/`
- `Inbox/`

When no better folder is given, default to:

- `Inbox/`

The skill should create missing folders instead of failing.

Update preference:

- If a matching note already exists in the chosen folder, prefer updating it instead of creating a duplicate.
- First match by filename.
- If filename does not match, try matching by normalized title.

Append preference:

- Use append mode when the user wants to keep earlier content and add a new section instead of replacing the whole note.

Daily Note preference:

- If the user asks to link a note into today's journal, prefer a normal note in the best content folder plus a wikilink from the daily note.
- First look for a daily folder among `Daily/`, `Daily Notes/`, `日记/`, `日志/`.
- If none exists, create `Daily/`.
