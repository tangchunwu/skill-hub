#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    SkillHubError,
    backup_dir,
    ensure_dir,
    find_target,
    iter_exported_skills,
    print_line,
    safe_symlink,
    skill_local_path,
    timestamp,
    copy_dir,
    expand_path,
)


def sync_skill(skill: dict, target_root: Path, mode: str, force: bool, backup_root: Path) -> tuple[str, str]:
    src = skill_local_path(skill)
    if not src.exists():
        raise SkillHubError(f"Skill source missing: {src}")
    dest = target_root / skill["canonical_name"]
    if dest.exists() and not force:
        return skill["id"], "skip_exists"
    backup = backup_dir(dest, backup_root, skill["canonical_name"]) if force else None
    if mode == "symlink":
        safe_symlink(src, dest)
    else:
        copy_dir(src, dest)
    if backup:
        return skill["id"], f"updated_backup={backup.name}"
    return skill["id"], "synced"


def main() -> None:
    parser = argparse.ArgumentParser(description="Export skills from skill-hub to target runtime.")
    parser.add_argument("--target", required=True, help="Target id from registry/sync-targets.yaml")
    parser.add_argument("--mode", choices=["copy", "symlink"], help="Override export mode")
    parser.add_argument("--force", action="store_true", help="Overwrite existing target directories")
    parser.add_argument("--skill", action="append", help="Only sync selected skill ids")
    args = parser.parse_args()

    try:
        target = find_target(args.target)
        if not target.get("enabled", False):
            raise SkillHubError(f"Target is disabled: {args.target}")
        root = expand_path(target["root"])
        ensure_dir(root)
        mode = args.mode or ("symlink" if target.get("export_mode") == "link-or-copy" else "copy")
        backup_root = root / ".skill-hub-backups" / timestamp()
        skills = iter_exported_skills()
        if args.skill:
            selected = set(args.skill)
            skills = [item for item in skills if item["id"] in selected or item["canonical_name"] in selected]

        if not skills:
            print_line("No skills selected.")
            return

        print_line(f"Sync target: {args.target}")
        print_line(f"Export root: {root}")
        print_line(f"Mode: {mode}")
        for skill in skills:
            skill_id, status = sync_skill(skill, root, mode, args.force, backup_root)
            print_line(f"- {skill_id}: {status}")
    except SkillHubError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
