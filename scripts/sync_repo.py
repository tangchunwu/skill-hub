#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from common import print_line, repo_root, run


def cmd_status(repo: Path) -> None:
    print_line(run(["git", "status", "--short"], cwd=repo).stdout or "working tree clean")
    print_line(run(["git", "log", "--oneline", "-1"], cwd=repo).stdout.strip())


def cmd_commit(repo: Path, message: str, push: bool) -> None:
    run(["git", "add", "."], cwd=repo)
    status = run(["git", "status", "--short"], cwd=repo).stdout.strip()
    if not status:
        print_line("No changes to commit.")
        return
    run(["git", "commit", "-m", message], cwd=repo)
    print_line(run(["git", "log", "--oneline", "-1"], cwd=repo).stdout.strip())
    if push:
        run(["git", "push", "origin", "main"], cwd=repo)
        print_line("Pushed to origin/main")


def cmd_rollback(repo: Path, target: str, push: bool) -> None:
    current = run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    print_line(f"Current HEAD: {current}")
    print_line(f"Rollback target: {target}")
    run(["git", "restore", "--source", target, "--staged", "--worktree", "."], cwd=repo)
    run(["git", "add", "."], cwd=repo)
    status = run(["git", "status", "--short"], cwd=repo).stdout.strip()
    if not status:
        print_line("Working tree already matches target commit.")
        return
    message = f"Rollback repository content to {target}"
    run(["git", "commit", "-m", message], cwd=repo)
    print_line(run(["git", "log", "--oneline", "-1"], cwd=repo).stdout.strip())
    if push:
        run(["git", "push", "origin", "main"], cwd=repo)
        print_line("Rollback commit pushed to origin/main")


def main() -> None:
    parser = argparse.ArgumentParser(description="Commit, push and rollback skill-hub safely.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status")

    commit_parser = subparsers.add_parser("commit")
    commit_parser.add_argument("--message", required=True)
    commit_parser.add_argument("--push", action="store_true")

    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("--to", required=True, help="Commit sha, tag or branch")
    rollback_parser.add_argument("--push", action="store_true")

    args = parser.parse_args()
    repo = repo_root()

    if args.command == "status":
        cmd_status(repo)
    elif args.command == "commit":
        cmd_commit(repo, args.message, args.push)
    elif args.command == "rollback":
        cmd_rollback(repo, args.to, args.push)


if __name__ == "__main__":
    main()
