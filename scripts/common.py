#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


class SkillHubError(Exception):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def registry_dir() -> Path:
    return repo_root() / "registry"


def load_yaml(path: Path) -> dict:
    if yaml is not None:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    else:
        result = subprocess.run(
            [
                "ruby",
                "-r",
                "yaml",
                "-r",
                "json",
                "-e",
                "puts JSON.generate(YAML.load_file(ARGV[0]))",
                str(path),
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise SkillHubError(f"Unable to parse yaml: {path}")
        data = json.loads(result.stdout or "{}")
    if not isinstance(data, dict):
        raise SkillHubError(f"Invalid yaml structure: {path}")
    return data


def load_skills() -> list[dict]:
    return load_yaml(registry_dir() / "skills.yaml").get("skills", [])


def load_targets() -> list[dict]:
    return load_yaml(registry_dir() / "sync-targets.yaml").get("targets", [])


def find_skill(skill_id: str) -> dict:
    for item in load_skills():
        if item.get("id") == skill_id or item.get("canonical_name") == skill_id:
            return item
    raise SkillHubError(f"Unknown skill: {skill_id}")


def find_target(target_id: str) -> dict:
    for item in load_targets():
        if item.get("id") == target_id:
            return item
    raise SkillHubError(f"Unknown target: {target_id}")


def expand_path(path_str: str) -> Path:
    return Path(os.path.expanduser(path_str)).resolve()


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise SkillHubError(result.stderr.strip() or "Command failed")
    return result


def print_line(message: str) -> None:
    print(message)


def copy_dir(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def backup_dir(src: Path, backup_root: Path, label: str) -> Path | None:
    if not src.exists():
        return None
    ensure_dir(backup_root)
    backup_path = backup_root / f"{label}_{timestamp()}"
    shutil.copytree(src, backup_path)
    return backup_path


def iter_exported_skills() -> list[dict]:
    items = []
    for skill in load_skills():
        local = skill.get("local", {})
        if local.get("exported", False):
            items.append(skill)
    return items


def skill_local_path(skill: dict) -> Path:
    path_str = skill.get("local", {}).get("path")
    if not path_str:
        raise SkillHubError(f"Missing local.path for {skill.get('id')}")
    return repo_root() / path_str


def download_file(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "skill-hub/1.0"})
    with urllib.request.urlopen(req) as response, dest.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    ensure_dir(dest_dir)
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(dest_dir)


def temp_dir(prefix: str) -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


def relative_to_repo(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root().resolve()))
    except Exception:
        return str(path)


def resolve_git_ref(repo: Path) -> str:
    return run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()


def git_status_short(repo: Path) -> str:
    return run(["git", "status", "--short"], cwd=repo).stdout.strip()


def safe_symlink(src: Path, dest: Path) -> None:
    if dest.exists() or dest.is_symlink():
        if dest.is_dir() and not dest.is_symlink():
            shutil.rmtree(dest)
        else:
            dest.unlink()
    dest.symlink_to(src, target_is_directory=True)


def abort(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)
