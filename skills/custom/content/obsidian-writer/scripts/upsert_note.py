#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


def yaml_scalar(value: str) -> str:
    escaped = (value or '').replace("'", "''")
    return f"'{escaped}'"


def ensure_markdown_filename(filename: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '-', (filename or '').strip())
    cleaned = re.sub(r'\s+', ' ', cleaned).strip().strip('.')
    if not cleaned:
        cleaned = '未命名笔记'
    if not cleaned.endswith('.md'):
        cleaned += '.md'
    return cleaned


def build_frontmatter(title: str, date: str, note_type: str, status: str, tags: list[str]) -> str:
    lines = [
        '---',
        f'title: {yaml_scalar(title)}',
        f'date: {yaml_scalar(date)}',
        f'type: {yaml_scalar(note_type)}',
        f'status: {yaml_scalar(status)}',
    ]
    if tags:
        lines.append('tags:')
        for tag in tags:
            lines.append(f'  - {yaml_scalar(tag)}')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


def normalize_text(value: str) -> str:
    return re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '', (value or '').strip().lower())


def extract_title(markdown: str) -> str:
    match = re.search(r'^title:\s*(.+)$', markdown, re.M)
    if not match:
        return ''
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
        if match.group(1).strip()[0] == "'":
            value = value.replace("''", "'")
    return value


def find_existing_note(folder: Path, filename: str, title: str) -> Path | None:
    exact = folder / filename
    if exact.exists():
        return exact

    target_stem = normalize_text(Path(filename).stem)
    target_title = normalize_text(title)

    for candidate in folder.glob('*.md'):
        if normalize_text(candidate.stem) == target_stem:
            return candidate

    for candidate in folder.glob('*.md'):
        try:
            content = candidate.read_text(encoding='utf-8')
        except Exception:
            continue
        if target_title and normalize_text(extract_title(content)) == target_title:
            return candidate

    return None


def split_frontmatter(markdown: str) -> tuple[str, str]:
    if not markdown.startswith('---\n'):
        return '', markdown
    parts = markdown.split('---\n', 2)
    if len(parts) < 3:
        return '', markdown
    return f'---\n{parts[1]}---\n\n', parts[2]


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
    parser = argparse.ArgumentParser(description='Create or update a Markdown note inside the local Obsidian vault.')
    parser.add_argument('--vault', default='/Users/tangchunwu/Documents/Obsidian Vault')
    parser.add_argument('--folder', required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--filename', required=True)
    parser.add_argument('--date', required=True)
    parser.add_argument('--type', dest='note_type', default='note')
    parser.add_argument('--status', default='done')
    parser.add_argument('--tags', default='')
    parser.add_argument('--content-file', required=True)
    parser.add_argument('--mode', choices=['auto', 'replace', 'append'], default='auto')
    args = parser.parse_args()

    vault = Path(args.vault)
    tags = [tag.strip() for tag in args.tags.split(',') if tag.strip()]
    folder_name = infer_folder(args.note_type, args.title, tags) if args.folder == 'auto' else args.folder
    folder = vault / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    content = Path(args.content_file).read_text(encoding='utf-8')
    filename = ensure_markdown_filename(args.filename)
    frontmatter = build_frontmatter(args.title, args.date, args.note_type, args.status, tags)
    note = frontmatter + content

    existing = find_existing_note(folder, filename, args.title)

    if args.mode == 'replace':
        target = existing or (folder / filename)
        existed = target.exists()
        target.write_text(note, encoding='utf-8')
        print(f'{"updated" if existed else "created"}:{target}')
        return

    if args.mode == 'append':
        target = existing or (folder / filename)
        if target.exists():
            previous = target.read_text(encoding='utf-8')
            old_frontmatter, old_body = split_frontmatter(previous)
            merged = (old_frontmatter or frontmatter) + old_body.rstrip() + '\n\n---\n\n' + content.strip() + '\n'
            target.write_text(merged, encoding='utf-8')
            print(f'appended:{target}')
            return
        target.write_text(note, encoding='utf-8')
        print(f'created:{target}')
        return

    target = existing or (folder / filename)
    existed = target.exists()
    target.write_text(note, encoding='utf-8')
    print(f'{"updated" if existed else "created"}:{target}')


if __name__ == '__main__':
    main()
