#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}

SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".zip",
    ".tgz",
    ".gz",
    ".tar",
    ".mp4",
    ".mov",
    ".ico",
}

SKIP_FILENAMES = {
    "all_skills_with_cn.json",
}

MAX_SCAN_BYTES = 2_000_000

PLACEHOLDER_WORDS = {
    "your",
    "example",
    "placeholder",
    "dummy",
    "sample",
    "test",
    "changeme",
    "replace",
    "todo",
    "你的",
    "示例",
    "占位",
}


@dataclass
class Finding:
    path: str
    line: int
    rule: str
    preview: str


RULES: list[tuple[str, re.Pattern[str]]] = [
    ("private-key-block", re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA |)?PRIVATE KEY-----")),
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{20,}\b")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")),
    ("bearer-token", re.compile(r"Authorization\s*:\s*Bearer\s+([A-Za-z0-9._~+/=-]{16,})", re.IGNORECASE)),
    ("imgbed-token", re.compile(r"\bimgbed_[A-Za-z0-9]{20,}\b")),
    (
        "secret-assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|bearer|client[_-]?secret|password|passwd|secret|token)\b"
            r"\s*[:=]\s*['\"]?([^'\"\s]{8,})"
        ),
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="扫描 skill 目录中的疑似硬编码密钥")
    parser.add_argument("--path", action="append", required=True, help="要扫描的文件或目录，可重复传入")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    findings: list[Finding] = []
    for raw in args.path:
        path = Path(raw).expanduser()
        if not path.exists():
            print(f"[WARN] 路径不存在，已跳过：{path}", file=sys.stderr)
            continue
        for file_path in iter_files(path):
            findings.extend(scan_file(file_path))

    if args.format == "json":
        print(json.dumps([finding.__dict__ for finding in findings], ensure_ascii=False, indent=2))
    else:
        print_text(findings)

    return 1 if findings else 0


def iter_files(path: Path):
    if path.is_file():
        if should_scan(path):
            yield path
        return

    for item in path.rglob("*"):
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        if item.is_file() and should_scan(item):
            yield item


def should_scan(path: Path) -> bool:
    if path.name in SKIP_FILENAMES:
        return False
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    try:
        return path.stat().st_size <= MAX_SCAN_BYTES
    except OSError:
        return False


def scan_file(path: Path) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return []
    except OSError:
        return []

    findings: list[Finding] = []
    for index, line in enumerate(text.splitlines(), 1):
        if is_safe_reference(line):
            continue
        for rule, pattern in RULES:
            match = pattern.search(line)
            if not match:
                continue
            secret_part = match.group(1) if match.groups() else match.group(0)
            if looks_like_placeholder(secret_part):
                continue
            findings.append(
                Finding(
                    path=str(path),
                    line=index,
                    rule=rule,
                    preview=redact_line(line),
                )
            )
    return findings


def is_safe_reference(line: str) -> bool:
    safe_markers = (
        "os.environ",
        "process.env",
        "Deno.env",
        "getenv(",
        "ENV[",
        "env var",
        "environment variable",
        "环境变量",
        "Bearer Token；默认读取",
        "你的",
        "示例",
    )
    if any(marker in line for marker in safe_markers):
        return True
    if re.search(r"\b(?:token|secret|password)\s*:\s*(?:list|dict|str|int|bool|Sequence|Iterable)\b", line):
        return True
    if re.search(r"\b(?:token|secret|password|pkey)\s*=\s*(?:params|metadata|os\.environ|os\.getenv|self|match|token_match)\b", line):
        return True
    if re.search(r"\b(?:password|token|secret)\s*=\s*[A-Za-z_][A-Za-z0-9_]*\b", line):
        return True
    if re.search(r"#\s*(?:password|token|secret)\s*:", line, re.IGNORECASE):
        return True
    return False


def looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(word in lowered for word in PLACEHOLDER_WORDS)


def redact_line(line: str) -> str:
    redacted = line.strip()
    redacted = re.sub(r"(Bearer\s+)[A-Za-z0-9._~+/=-]{8,}", r"\1<REDACTED>", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{8,}\b", "sk-<REDACTED>", redacted)
    redacted = re.sub(r"\bsk-ant-[A-Za-z0-9_-]{8,}\b", "sk-ant-<REDACTED>", redacted)
    redacted = re.sub(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{8,}\b", "ghp_<REDACTED>", redacted)
    redacted = re.sub(r"\bimgbed_[A-Za-z0-9]{8,}\b", "imgbed_<REDACTED>", redacted)
    redacted = re.sub(r"(['\"])[^'\"]{16,}\1", r"\1<REDACTED>\1", redacted)
    return redacted[:240]


def print_text(findings: list[Finding]) -> None:
    if not findings:
        print("OK: 未发现疑似硬编码密钥")
        return

    print(f"发现 {len(findings)} 处疑似硬编码密钥：")
    for finding in findings:
        print(f"- {finding.path}:{finding.line} [{finding.rule}] {finding.preview}")
    print()
    print("处理建议：把真实值移到环境变量或系统凭据中，skill 里只保留变量名和读取逻辑。")


if __name__ == "__main__":
    raise SystemExit(main())
