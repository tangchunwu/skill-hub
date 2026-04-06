#!/usr/bin/env python3
import argparse
import json
import mimetypes
import re
import time
import urllib.request
from pathlib import Path


CONFIG_PATH = Path.home() / ".flow2api-imagegen" / "config.json"


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_payload(args, config):
    preset_model = config.get("video_models", {}).get(args.preset) if args.preset else None
    model = args.model or preset_model or config["video_default_model"]
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": True,
    }
    return payload, model


def extract_video_url(text):
    patterns = [
        r"<video[^>]+src=['\"]([^'\"]+)['\"]",
        r'"url"\s*:\s*"([^"]+\.mp4[^"]*)"',
        r"(https?://[^\s'\"]+\.mp4[^\s'\"]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def download_video(url):
    with urllib.request.urlopen(url, timeout=1800) as resp:
        content_type = resp.headers.get("Content-Type", "video/mp4")
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip()) or ".mp4"
        return resp.read(), ext.lstrip(".")


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
    with urllib.request.urlopen(req, timeout=1800) as resp:
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


def should_retry(text):
    retry_markers = [
        "INTERNAL，请重试",
        "INTERNAL, please retry",
        "视频生成失败: INTERNAL",
        "reCAPTCHA evaluation failed",
        "PUBLIC_ERROR_SOMETHING_WENT_WRONG",
    ]
    return any(marker in text for marker in retry_markers)


def main():
    parser = argparse.ArgumentParser(description="Generate video with Flow2API")
    parser.add_argument("--prompt", "-p", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument(
        "--preset",
        choices=["landscape", "portrait"],
        default=None,
    )
    parser.add_argument("--model", "-m")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config = load_config()
    payload, model = build_payload(args, config)
    body = json.dumps(payload).encode("utf-8")

    final_text = ""
    for attempt in range(3):
        final_text = request_stream(config["base_url"], config["api_key"], body)
        video_url = extract_video_url(final_text)
        if video_url:
            break
        if should_retry(final_text) and attempt < 2:
            time.sleep(3)
            continue
        break
    video_url = extract_video_url(final_text)
    if not video_url:
        raise SystemExit(f"生成失败: {config['base_url']}: 未拿到视频链接，响应={final_text!r}")

    video_bytes, ext = download_video(video_url)
    output_path = Path(args.output).expanduser().resolve()
    if output_path.suffix == "":
        output_path = output_path.with_suffix("." + ext)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(video_bytes)

    result = {
        "ok": True,
        "model": model,
        "base_url": config["base_url"],
        "video_url": video_url,
        "output": str(output_path),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"生成成功: {output_path}")
        print(f"模型: {model}")


if __name__ == "__main__":
    main()
