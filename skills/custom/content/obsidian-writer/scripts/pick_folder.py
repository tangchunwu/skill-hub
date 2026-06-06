#!/usr/bin/env python3
import argparse
from pathlib import Path


def infer_folder(note_type: str, title: str, tags: list[str]) -> str:
    text = f'{note_type} {title} {" ".join(tags)}'.lower()

    if any(keyword in text for keyword in ['复盘', 'review', 'retrospective']):
        return '复盘'
    if any(keyword in text for keyword in ['产品', 'prd', 'strategy', 'roadmap']):
        return '产品'
    if any(keyword in text for keyword in ['技术', 'debug', 'fix', '工程', '排查']):
        return '技术'
    if any(keyword in text for keyword in ['todo', '待办', 'task', 'action']):
        return '待办'
    if any(keyword in text for keyword in ['日报', 'daily', 'journal', '日记']):
        return 'Daily'
    return 'Inbox'


def main() -> None:
    parser = argparse.ArgumentParser(description='Pick a reasonable Obsidian folder for a note.')
    parser.add_argument('--vault', default='/Users/tangchunwu/Documents/Obsidian Vault')
    parser.add_argument('--type', dest='note_type', default='note')
    parser.add_argument('--title', default='')
    parser.add_argument('--tags', default='')
    args = parser.parse_args()

    tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()]
    folder = infer_folder(args.note_type, args.title, tags)
    target = Path(args.vault) / folder
    target.mkdir(parents=True, exist_ok=True)
    print(folder)


if __name__ == '__main__':
    main()
