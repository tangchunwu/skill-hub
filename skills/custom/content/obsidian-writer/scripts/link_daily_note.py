#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


COMMON_DAILY_FOLDERS = ['Daily', 'Daily Notes', '日记', '日志']


def ensure_markdown_filename(filename: str) -> str:
    if filename.endswith('.md'):
        return filename
    return f'{filename}.md'


def find_daily_folder(vault: Path, explicit: str | None) -> Path:
    if explicit:
        target = vault / explicit
        target.mkdir(parents=True, exist_ok=True)
        return target

    for folder_name in COMMON_DAILY_FOLDERS:
        candidate = vault / folder_name
        if candidate.exists():
            return candidate

    target = vault / COMMON_DAILY_FOLDERS[0]
    target.mkdir(parents=True, exist_ok=True)
    return target


def ensure_heading(content: str, heading: str) -> str:
    normalized = content.rstrip()
    pattern = re.compile(rf'(?m)^##\s+{re.escape(heading)}\s*$')
    if pattern.search(normalized):
        return normalized + '\n'
    if not normalized:
        return f'## {heading}\n'
    return normalized + f'\n\n## {heading}\n'


def insert_link(content: str, heading: str, link_line: str) -> tuple[str, bool]:
    content = ensure_heading(content, heading)
    if link_line in content:
        return content, False

    lines = content.splitlines()
    heading_index = next((index for index, line in enumerate(lines) if line.strip() == f'## {heading}'), None)
    if heading_index is None:
        lines.extend(['', f'## {heading}', link_line])
        return '\n'.join(lines).rstrip() + '\n', True

    insert_at = heading_index + 1
    while insert_at < len(lines) and lines[insert_at].startswith('- '):
        insert_at += 1
    lines.insert(insert_at, link_line)
    return '\n'.join(lines).rstrip() + '\n', True


def main() -> None:
    parser = argparse.ArgumentParser(description='Link a note into an Obsidian daily note.')
    parser.add_argument('--vault', default='/Users/tangchunwu/Documents/Obsidian Vault')
    parser.add_argument('--date', required=True)
    parser.add_argument('--note-path', required=True)
    parser.add_argument('--heading', default='今天的记录')
    parser.add_argument('--daily-folder', default='')
    parser.add_argument('--label', default='')
    args = parser.parse_args()

    vault = Path(args.vault)
    daily_folder = find_daily_folder(vault, args.daily_folder or None)
    daily_note = daily_folder / ensure_markdown_filename(args.date)

    note_path = Path(args.note_path)
    link_target = note_path.stem
    link_text = args.label.strip() or link_target
    link_line = f'- [[{link_target}|{link_text}]]'

    previous = daily_note.read_text(encoding='utf-8') if daily_note.exists() else ''
    updated, changed = insert_link(previous, args.heading, link_line)
    daily_note.write_text(updated, encoding='utf-8')
    print(f'{"updated" if changed else "unchanged"}:{daily_note}')


if __name__ == '__main__':
    main()
