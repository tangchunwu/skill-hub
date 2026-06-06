#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
import sys
import uuid
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_BASE_URL = "https://openclaw-tu.us.ci"


def main() -> int:
    parser = argparse.ArgumentParser(description="直连 openclaw-tu 图床上传图片")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("healthcheck", help="检查必要环境变量")
    upload = subparsers.add_parser("upload", help="上传图片并返回 URL")
    upload.add_argument("--file", required=True, help="本地图片路径")
    upload.add_argument("--url", default=os.environ.get("IMGBED_UPLOAD_URL"), help="上传接口地址")
    upload.add_argument("--base-url", default=os.environ.get("IMGBED_BASE_URL", DEFAULT_BASE_URL), help="图床基础 URL")
    upload.add_argument("--token", default=os.environ.get("IMGBED_TOKEN"), help="Bearer Token；默认读取 IMGBED_TOKEN")
    upload.add_argument("--field-name", default=os.environ.get("IMGBED_FIELD_NAME", "file"), help="上传字段名")
    args = parser.parse_args()

    if args.command == "healthcheck":
        if not os.environ.get("IMGBED_TOKEN"):
            print("[ERROR] 缺少 IMGBED_TOKEN", file=sys.stderr)
            return 1
        print(json.dumps({"success": True, "baseUrl": os.environ.get("IMGBED_BASE_URL", DEFAULT_BASE_URL)}, ensure_ascii=False))
        return 0

    upload_url = args.url or args.base_url.rstrip("/") + "/upload"
    if not args.token:
        print("[ERROR] 缺少 IMGBED_TOKEN", file=sys.stderr)
        return 1

    image_path = Path(args.file)
    if not image_path.is_file():
        print(f"[ERROR] 图片不存在：{image_path}", file=sys.stderr)
        return 1

    try:
        response_text = upload_file(upload_url, args.token, args.field_name, image_path)
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        print(f"[ERROR] 上传失败 HTTP {exc.code}: {text}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"[ERROR] 上传失败：{exc}", file=sys.stderr)
        return 1

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        parsed = response_text

    url = extract_url(parsed, args.base_url)
    if not url:
        print(json.dumps({"success": False, "response": parsed}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps({"success": True, "url": url, "response": parsed}, ensure_ascii=False))
    return 0


def upload_file(upload_url: str, token: str, field_name: str, image_path: Path) -> str:
    boundary = "----openclaw-tu-" + uuid.uuid4().hex
    content_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
    filename = image_path.name
    file_bytes = image_path.read_bytes()

    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)
    request = urllib.request.Request(
        upload_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "User-Agent": "curl/8.7.1",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_url(value, base_url: str) -> str:
    if isinstance(value, list):
        for item in value:
            found = extract_url(item, base_url)
            if found:
                return found
        return ""

    if isinstance(value, dict):
        for key in ("url", "src", "href", "path"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return absolutize(candidate, base_url)
        for item in value.values():
            found = extract_url(item, base_url)
            if found:
                return found
        return ""

    if isinstance(value, str) and value.startswith(("http://", "https://", "/")):
        return absolutize(value, base_url)

    return ""


def absolutize(url: str, base_url: str) -> str:
    if url.startswith(("http://", "https://")):
        return url
    return base_url.rstrip("/") + "/" + url.lstrip("/")


if __name__ == "__main__":
    raise SystemExit(main())
