#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or update Wave background presets and optionally set the global tab preset."
    )
    parser.add_argument("--config-dir", default="~/.config/waveterm")
    parser.add_argument("--preset", required=True, help="Preset key like bg@cloud")
    parser.add_argument("--display-name", help="Preset display:name")
    parser.add_argument("--image", help="Local image path used to build the CSS background")
    parser.add_argument("--bg", help="Raw CSS background value; overrides --image")
    parser.add_argument("--opacity", type=float, help="Background opacity from 0.0 to 1.0")
    parser.add_argument("--set-global", action="store_true", help="Write tab:preset to settings.json")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing files")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any], *, dry_run: bool) -> Path | None:
    if dry_run:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        backup = path.with_name(f"{path.name}.bak_{time.strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(path, backup)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return backup


def build_bg(args: argparse.Namespace) -> str | None:
    if args.bg:
        return args.bg
    if args.image:
        image_path = Path(args.image).expanduser().resolve()
        return f"url('{image_path}') center/cover no-repeat"
    return None


def ensure_opacity(opacity: float | None) -> None:
    if opacity is None:
        return
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("--opacity must be between 0.0 and 1.0")


def default_display_name(preset: str) -> str:
    if "@" in preset:
        return preset.split("@", 1)[1]
    return preset


def update_preset_blob(
    existing: dict[str, Any] | None,
    *,
    display_name: str | None,
    bg_value: str | None,
    opacity: float | None,
) -> dict[str, Any]:
    preset = dict(existing or {})
    if not preset and not (display_name or bg_value):
        raise ValueError("Creating a new preset requires --display-name and --image/--bg, or reuse an existing preset.")
    preset.setdefault("bg:*", True)
    if display_name:
        preset["display:name"] = display_name
    else:
        preset.setdefault("display:name", "Wave Background")
    if bg_value:
        preset["bg"] = bg_value
    if opacity is not None:
        preset["bg:opacity"] = opacity
    return preset


def main() -> int:
    args = parse_args()
    try:
        ensure_opacity(args.opacity)
        if not args.preset.startswith("bg@"):
            raise ValueError("--preset should usually look like bg@cloud")
        config_dir = Path(args.config_dir).expanduser().resolve()
        settings_path = config_dir / "settings.json"
        backgrounds_path = config_dir / "backgrounds.json"
        presets_path = config_dir / "presets" / "bg.json"

        settings = read_json(settings_path)
        backgrounds = read_json(backgrounds_path)
        presets = read_json(presets_path)

        bg_value = build_bg(args)
        display_name = args.display_name or None
        existing = backgrounds.get(args.preset) or presets.get(args.preset)
        preset_blob = update_preset_blob(
            existing,
            display_name=display_name or (default_display_name(args.preset) if not existing else None),
            bg_value=bg_value,
            opacity=args.opacity,
        )

        backgrounds[args.preset] = preset_blob
        presets[args.preset] = preset_blob

        if args.set_global:
            settings["tab:preset"] = args.preset

        targets = [
            ("backgrounds.json", backgrounds_path, backgrounds),
            ("presets/bg.json", presets_path, presets),
        ]
        if args.set_global:
            targets.append(("settings.json", settings_path, settings))

        print("Wave background update")
        print(f"config_dir={config_dir}")
        print(f"preset={args.preset}")
        print(f"dry_run={args.dry_run}")

        for label, path, payload in targets:
            backup = write_json(path, payload, dry_run=args.dry_run)
            reloaded = payload if args.dry_run else read_json(path)
            print(f"\n[{label}] {path}")
            if backup:
                print(f"backup={backup}")
            if label == "settings.json":
                print(json.dumps({"tab:preset": reloaded.get("tab:preset")}, ensure_ascii=False, indent=2))
            else:
                print(json.dumps(reloaded.get(args.preset, {}), ensure_ascii=False, indent=2))

        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
