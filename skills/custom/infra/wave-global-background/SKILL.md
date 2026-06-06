---
name: wave-global-background
description: Configure Wave Terminal / WaveTerm global tab background defaults by editing ~/.config/waveterm/settings.json, backgrounds.json, and presets/bg.json. Use when Codex needs to make a background preset global, set or change a Wave background image, tweak background opacity, or explain how Wave tab backgrounds are wired.
---

# Wave Global Background

Use this skill to inspect or update Wave's global tab background configuration with minimal, reversible edits.

## Workflow

1. Inspect the current files under `~/.config/waveterm/`:
   - `settings.json`
   - `backgrounds.json`
   - `presets/bg.json`
2. Reuse an existing preset when possible. Create a new preset only when the user wants a different image or key.
3. Run `scripts/update_wave_background.py` to make the change and create timestamped backups.
4. Re-read the touched JSON files to verify the result.
5. Tell the user that `tab:preset` controls the global default for new tabs; existing tabs may need reapplying the preset or restarting Wave.

## Preferred command

Run the helper from the skill directory.

```bash
python3 scripts/update_wave_background.py \
  --preset bg@cloud \
  --opacity 0.6 \
  --set-global
```

## Common variants

Set a new image and make it global:

```bash
python3 scripts/update_wave_background.py \
  --preset bg@cloud \
  --display-name 云彩壁纸 \
  --image ~/Downloads/wavebackground.png \
  --opacity 0.6 \
  --set-global
```

Use raw CSS background instead of an image path:

```bash
python3 scripts/update_wave_background.py \
  --preset bg@aurora \
  --display-name 极光 \
  --bg "linear-gradient(180deg, #0f172a 0%, #1d4ed8 100%)" \
  --opacity 0.55 \
  --set-global
```

Preview changes without writing files:

```bash
python3 scripts/update_wave_background.py --preset bg@cloud --opacity 0.55 --dry-run
```

## Rules

- Prefer local image files over remote URLs.
- Use absolute paths in the generated `bg` CSS. `~` is okay on input; resolve it before writing.
- Keep `bg:*: true` on background presets so old per-tab background keys do not leak through.
- Mirror the preset into both `backgrounds.json` and `presets/bg.json` for compatibility with Wave's preset loading and migrated setups.
- If the preset already exists and the user only asked for opacity/global changes, do not rewrite unrelated fields.
- Always report touched files and backup paths.
