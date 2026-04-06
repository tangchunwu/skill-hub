#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import urllib.request
from pathlib import Path


CONFIG_PATH = Path.home() / ".flow2api-imagegen" / "config.json"


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_payload(args, config):
    preset_model = config["models"].get(args.preset) if args.preset else None
    model = args.model or preset_model or config["default_model"]
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": True,
    }
    return payload, model


def download_image(url):
    with urllib.request.urlopen(url, timeout=300) as resp:
        content_type = resp.headers.get("Content-Type", "image/png")
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".png"
        return resp.read(), ext.lstrip(".")


def extract_markdown_image_url(text):
    match = re.search(r"!\[[^\]]*\]\((.*?)\)", text)
    return match.group(1) if match else None


def extract_json_image_url(text):
    match = re.search(r'"url"\s*:\s*"([^"]+)"', text)
    return match.group(1) if match else None


def request_stream(base_url, api_key, body):
    req = urllib.request.Request(
        url=base_url.rstrip("/") + "/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    chunks = []
    with urllib.request.urlopen(req, timeout=300) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8", "ignore").strip()
            if not line or not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                break
            event = json.loads(data)
            choice = (event.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}
            for key in ("reasoning_content", "content"):
                value = delta.get(key)
                if isinstance(value, str) and value:
                    chunks.append(value)
    return "".join(chunks).strip()


def main():
    parser = argparse.ArgumentParser(description="Generate image with Flow2API")
    parser.add_argument("--prompt", "-p", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument(
        "--preset",
        choices=["square", "landscape", "portrait", "four_three", "three_four"],
        default=None,
    )
    parser.add_argument("--model", "-m")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config = load_config()
    payload, model = build_payload(args, config)
    body = json.dumps(payload).encode("utf-8")

    endpoints = [config["base_url"]]
    if config.get("enable_fallback"):
        fallback_base_url = config.get("fallback_base_url")
        if fallback_base_url and fallback_base_url not in endpoints:
            endpoints.append(fallback_base_url)

    last_error = None
    final_text = ""
    image_url = None
    used_base_url = None
    for endpoint in endpoints:
        try:
            candidate_text = request_stream(endpoint, config["api_key"], body)
        except Exception as exc:
            last_error = f"{endpoint}: {exc}"
            continue

        candidate_image_url = extract_markdown_image_url(candidate_text) or extract_json_image_url(candidate_text)
        if candidate_image_url:
            final_text = candidate_text
            image_url = candidate_image_url
            used_base_url = endpoint
            break

        last_error = f"{endpoint}: 未拿到图片链接，响应={candidate_text!r}"

    if not image_url:
        raise SystemExit(f"生成失败: {last_error or f'未拿到图片链接，最后响应={final_text!r}'}")

    if image_url.startswith("data:image"):
        match = re.search(r"^data:image/([^;]+);base64,(.+)$", image_url)
        if not match:
            raise SystemExit("生成失败: 无法解析 base64 图片")
        ext = match.group(1)
        image_bytes = base64.b64decode(match.group(2))
    else:
        image_bytes, ext = download_image(image_url)

    output_path = Path(args.output).expanduser().resolve()
    if output_path.suffix == "":
        output_path = output_path.with_suffix("." + ext)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)

    result = {
        "ok": True,
        "model": model,
        "base_url": used_base_url,
        "image_url": image_url,
        "output": str(output_path),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"生成成功: {output_path}")
        print(f"模型: {model}")


if __name__ == "__main__":
    main()
