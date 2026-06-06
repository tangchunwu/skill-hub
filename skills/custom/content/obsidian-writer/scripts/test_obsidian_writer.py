#!/usr/bin/env python3
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
UPSERT = ROOT / 'upsert_note.py'
LINK = ROOT / 'link_daily_note.py'


def run(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def write_temp_content(tmpdir: Path, name: str, content: str) -> Path:
    path = tmpdir / name
    path.write_text(content, encoding='utf-8')
    return path


def assert_contains(path: Path, expected: str) -> None:
    content = path.read_text(encoding='utf-8')
    assert expected in content, f'missing "{expected}" in {path}'


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix='obsidian-writer-test-'))
    try:
        vault = temp_root / 'vault'
        vault.mkdir(parents=True, exist_ok=True)

        first = write_temp_content(temp_root, 'first.md', '# A\n')
        output = run(
            'python3', str(UPSERT),
            '--vault', str(vault),
            '--folder', 'auto',
            '--title', '技术: 记录',
            '--filename', '技术:记录',
            '--date', '2026-04-17',
            '--type', 'summary',
            '--status', 'done',
            '--tags', '技术,排查',
            '--content-file', str(first),
            '--mode', 'auto',
        )
        created_path = Path(output.split(':', 1)[1])
        assert created_path.name == '技术-记录.md'
        assert created_path.parent.name == '技术'
        assert_contains(created_path, "title: '技术: 记录'")

        second = write_temp_content(temp_root, 'second.md', '# B\n')
        output = run(
            'python3', str(UPSERT),
            '--vault', str(vault),
            '--folder', '技术',
            '--title', '技术: 记录',
            '--filename', '不同名字.md',
            '--date', '2026-04-17',
            '--type', 'summary',
            '--status', 'done',
            '--tags', '技术',
            '--content-file', str(second),
            '--mode', 'auto',
        )
        assert output.startswith('updated:')
        assert_contains(created_path, '# B')

        append = write_temp_content(temp_root, 'append.md', '追加内容\n')
        output = run(
            'python3', str(UPSERT),
            '--vault', str(vault),
            '--folder', '技术',
            '--title', '技术: 记录',
            '--filename', created_path.name,
            '--date', '2026-04-17',
            '--type', 'summary',
            '--status', 'done',
            '--tags', '技术',
            '--content-file', str(append),
            '--mode', 'append',
        )
        assert output.startswith('appended:')
        assert_contains(created_path, '追加内容')

        output = run(
            'python3', str(LINK),
            '--vault', str(vault),
            '--date', '2026-04-17',
            '--note-path', str(created_path),
            '--heading', '今天的记录',
            '--label', '技术记录',
        )
        daily_note = Path(output.split(':', 1)[1])
        assert daily_note.name == '2026-04-17.md'
        assert_contains(daily_note, '## 今天的记录')
        assert_contains(daily_note, '[[技术-记录|技术记录]]')

        output = run(
            'python3', str(LINK),
            '--vault', str(vault),
            '--date', '2026-04-17',
            '--note-path', str(created_path),
            '--heading', '今天的记录',
            '--label', '技术记录',
        )
        assert output.startswith('unchanged:')
        print('ok')
    finally:
        shutil.rmtree(temp_root)


if __name__ == '__main__':
    main()
