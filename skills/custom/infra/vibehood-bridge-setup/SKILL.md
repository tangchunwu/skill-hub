---
name: vibehood-bridge-setup
description: One-shot setup for VibeHood hooks/bridge (Codex CLI + Codex Desktop + Gemini CLI)
---

# VibeHood Bridge Setup

This skill installs and configures VibeHood integration for:
- Claude Code (hooks -> wrapper -> `vibehood-bridge --source claude`)
- Codex CLI (hooks -> `vibehood-bridge --source codex`)
- Codex Desktop (tail `~/.codex/logs_2.sqlite` -> emit Codex hook payloads -> VibeHood)
- Gemini CLI (hooks -> `vibehood-bridge --source gemini`, with sane timeouts)

## Install

Copy this folder to your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R codex-skills/vibehood-bridge-setup ~/.codex/skills/vibehood-bridge-setup
```

## Usage

When the user invokes this skill, run the installer script once:

```bash
python3 ~/.codex/skills/vibehood-bridge-setup/scripts/setup.py
```

Then verify quickly:

```bash
launchctl list | rg 'com\\.vibehood\\.codex-desktop-bridge' || true
python3 -c "import json, pathlib; d=json.loads((pathlib.Path.home()/'.gemini/settings.json').read_text()); print('gemini SessionStart timeouts', [h['hooks'][0].get('timeout') for h in d.get('hooks',{}).get('SessionStart',[]) if isinstance(h,dict) and isinstance(h.get('hooks'),list) and h['hooks'] and isinstance(h['hooks'][0],dict) and 'vibehood-bridge-gemini-hook' in h['hooks'][0].get('command','')])"
```

## What It Does

- Writes/updates:
  - `~/.gemini/settings.json` (adds hooks, sets timeout to 2000ms)
  - `~/.codex/hooks.json` (adds Codex CLI hooks for prompt + tools)
- Creates/updates:
  - `~/.vibehood/bin/vibehood-bridge-gemini-hook`
  - `~/.vibehood/bin/vibehood-bridge-codex-desktop`
  - `~/Library/LaunchAgents/com.vibehood.codex-desktop-bridge.plist` (macOS LaunchAgent)
- Starts the LaunchAgent so Codex Desktop is monitored continuously.

## Preconditions

- VibeHood must be installed and opened at least once (to ensure `~/.vibehood/bin/vibehood-bridge` exists).
- Claude Code integration requires Claude Code to be installed (it patches `~/.claude/hooks/hooks.json` if present).
