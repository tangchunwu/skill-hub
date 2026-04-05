#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
import os
import shutil
from pathlib import Path

from common import (
    SkillHubError,
    backup_dir,
    ensure_dir,
    find_target,
    iter_exported_skills,
    load_targets,
    print_line,
    skill_local_path,
    timestamp,
    copy_dir,
    expand_path,
)


IGNORE_NAMES = {
    ".DS_Store",
    "__pycache__",
}


def _filtered_entries(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(name for name in os.listdir(path) if name not in IGNORE_NAMES)


def dirs_equal(left: Path, right: Path) -> bool:
    if not left.exists() or not right.exists():
        return False

    cmp = filecmp.dircmp(left, right, ignore=list(IGNORE_NAMES))
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(left, right, cmp.common_files, shallow=False)
    if mismatch or errors:
        return False
    for subdir in cmp.common_dirs:
        if not dirs_equal(left / subdir, right / subdir):
            return False
    return True


def ingest_skill(skill: dict, target_root: Path, force: bool, backup_root: Path, dry_run: bool) -> tuple[str, str]:
    dest = target_root / skill["canonical_name"]
    src = skill_local_path(skill)

    if not dest.exists():
        return skill["id"], "skip_missing"

    if dest.is_symlink():
        try:
            if dest.resolve() == src.resolve():
                return skill["id"], "skip_linked"
        except FileNotFoundError:
            pass

    if src.exists() and dirs_equal(dest, src):
        return skill["id"], "skip_unchanged"

    if dry_run:
        return skill["id"], "would_ingest"

    ensure_dir(src.parent)
    backup = backup_dir(src, backup_root, skill["canonical_name"]) if src.exists() else None
    copy_dir(dest, src)
    if backup:
        return skill["id"], f"ingested_backup={backup.name}"
    return skill["id"], "ingested"


def run_target(target: dict, selected_skills: list[str] | None, force: bool, dry_run: bool) -> None:
    target_root = expand_path(target["root"])
    skills = iter_exported_skills()
    if selected_skills:
        selected = set(selected_skills)
        skills = [item for item in skills if item["id"] in selected or item["canonical_name"] in selected]

    if not skills:
        print_line(f"[{target['id']}] No skills selected.")
        return

    backup_root = Path(__file__).resolve().parent.parent / ".backups" / "ingest" / target["id"] / timestamp()
    print_line(f"Ingest target: {target['id']}")
    print_line(f"Source root: {target_root}")
    for skill in skills:
        skill_id, status = ingest_skill(skill, target_root, force, backup_root, dry_run)
        print_line(f"- {skill_id}: {status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull local runtime skill changes back into skill-hub.")
    parser.add_argument("--target", required=True, help="Target id from registry/sync-targets.yaml or 'all'")
    parser.add_argument("--skill", action="append", help="Only ingest selected skill ids")
    parser.add_argument("--force", action="store_true", help="Reserved for future conflict policy; currently informational")
    parser.add_argument("--dry-run", action="store_true", help="Only print what would be ingested")
    args = parser.parse_args()

    try:
        if args.target == "all":
            targets = [item for item in load_targets() if item.get("enabled", False)]
            if not targets:
                raise SkillHubError("No enabled targets found.")
            for index, target in enumerate(targets):
                if index > 0:
                    print_line("")
                run_target(target, args.skill, args.force, args.dry_run)
        else:
            target = find_target(args.target)
            if not target.get("enabled", False):
                raise SkillHubError(f"Target is disabled: {args.target}")
            run_target(target, args.skill, args.force, args.dry_run)
    except SkillHubError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
