#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_URL = "https://mianhua.me/api/blog/external/upsert"


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"[ERROR] JSON 格式错误：{exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("[ERROR] 博客内容必须是单个 JSON 对象")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="直连个人博客 upsert 接口发布文章")
    parser.add_argument("--json-file", required=True, help="博客 JSON 文件路径")
    parser.add_argument("--url", default=os.environ.get("BLOG_UPSERT_URL", DEFAULT_URL), help="博客 upsert API 地址")
    parser.add_argument("--token", default=os.environ.get("BLOG_UPSERT_TOKEN"), help="Bearer Token；默认读取 BLOG_UPSERT_TOKEN")
    args = parser.parse_args()

    if not args.token:
        raise SystemExit("[ERROR] 缺少 BLOG_UPSERT_TOKEN")

    payload = load_json(Path(args.json_file))
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        args.url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {args.token}",
            "User-Agent": "curl/8.7.1",
            "Accept": "*/*",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            text = response.read().decode("utf-8", errors="replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        print(f"[ERROR] 发布失败 HTTP {exc.code}: {text}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"[ERROR] 发布失败：{exc}", file=sys.stderr)
        return 1

    print(json.dumps({"success": True, "status": status, "response": parse_response(text)}, ensure_ascii=False))
    return 0


def parse_response(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


if __name__ == "__main__":
    raise SystemExit(main())
