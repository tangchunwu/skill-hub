#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from common import (
    SkillHubError,
    backup_dir,
    copy_dir,
    download_file,
    ensure_dir,
    extract_zip,
    iter_exported_skills,
    load_skills,
    print_line,
    repo_root,
    run,
    skill_local_path,
    temp_dir,
)


def update_from_github(skill: dict, work_dir: Path) -> tuple[Path, str]:
    source = skill["source"]
    owner = source["owner"]
    repo = source["repo"]
    ref = source.get("ref", "main")
    path = source["path"]
    clone_dir = work_dir / f"{owner}-{repo}"
    run(["git", "clone", "--depth", "1", "--branch", ref, f"https://github.com/{owner}/{repo}.git", str(clone_dir)])
    src_dir = clone_dir / path
    if not src_dir.exists():
        raise SkillHubError(f"Missing upstream path: {path}")
    sha = run(["git", "rev-parse", "HEAD"], cwd=clone_dir).stdout.strip()
    return src_dir, sha


def update_from_download(skill: dict, work_dir: Path) -> tuple[Path, str]:
    source = skill["source"]
    url = source["url"]
    zip_path = work_dir / "download.zip"
    extract_dir = work_dir / "extract"
    download_file(url, zip_path)
    extract_zip(zip_path, extract_dir)
    children = [item for item in extract_dir.iterdir() if item.is_dir()]
    if len(children) != 1:
        raise SkillHubError(f"Unexpected zip layout for {skill['id']}")
    src_dir = children[0]
    return src_dir, url


def refresh_skill(skill: dict, backup_root: Path) -> tuple[str, str]:
    provider = skill.get("source", {}).get("provider")
    tmp = temp_dir(f"skill-hub-{skill['id']}-")
    try:
        if provider == "github":
            upstream_dir, ref_info = update_from_github(skill, tmp)
        elif provider == "direct-download":
            upstream_dir, ref_info = update_from_download(skill, tmp)
        else:
            raise SkillHubError(f"Unsupported provider: {provider}")

        local_dir = skill_local_path(skill)
        ensure_dir(local_dir.parent)
        backup = backup_dir(local_dir, backup_root, skill["canonical_name"])
        copy_dir(upstream_dir, local_dir)
        label = backup.name if backup else "none"
        return skill["id"], f"updated ref={ref_info} backup={label}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh upstream skills into skill-hub.")
    parser.add_argument("--all", action="store_true", help="Update all upstream skills")
    parser.add_argument("--skill", action="append", help="Only update selected skill ids")
    parser.add_argument("--dry-run", action="store_true", help="Only print selected skills")
    args = parser.parse_args()

    skills = [item for item in load_skills() if item.get("type") == "upstream"]
    if args.skill:
        selected = set(args.skill)
        skills = [item for item in skills if item["id"] in selected or item["canonical_name"] in selected]
    elif not args.all:
        raise SystemExit("ERROR: use --all or --skill <id>")

    if args.dry_run:
        for skill in skills:
            print_line(f"- {skill['id']}: {skill['source']['provider']}")
        return

    backup_root = repo_root() / ".backups" / "upstream" / repo_root().name
    ensure_dir(backup_root)
    for skill in skills:
        try:
            skill_id, status = refresh_skill(skill, backup_root)
            print_line(f"- {skill_id}: {status}")
        except SkillHubError as exc:
            print_line(f"- {skill['id']}: ERROR {exc}")


if __name__ == "__main__":
    main()
