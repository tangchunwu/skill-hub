#!/usr/bin/python3
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


CODEX_LOG_DB = Path.home() / ".codex" / "logs_2.sqlite"
BRIDGE = Path.home() / ".vibehood" / "bin" / "vibehood-bridge"
STATE_DIR = Path.home() / ".vibehood" / "state"
STATE_PATH = STATE_DIR / "codex-desktop-bridge.json"

CODEX_APPSERVER_PGREP = ["pgrep", "-f", "Codex.app/Contents/Resources/codex app-server"]
CODEX_APPSERVER_PS = ["ps", "ax", "-o", "pid=,command="]


def _safe_json_loads(s: str) -> Optional[dict[str, Any]]:
    try:
        v = json.loads(s)
        return v if isinstance(v, dict) else None
    except Exception:
        return None


def _extract_json_after_marker(body: str, marker: str) -> Optional[dict[str, Any]]:
    idx = body.find(marker)
    if idx < 0:
        return None
    js = body[idx + len(marker) :].strip()
    return _safe_json_loads(js)


def _extract_turn_id(body: str) -> Optional[str]:
    m = re.search(r"(?:turn_id=|turn\.id=)([0-9a-fA-F-]{36})", body)
    return m.group(1) if m else None


def _extract_cwd(body: str) -> Optional[str]:
    m = re.search(r"cwd=([^\s}]+)", body)
    return m.group(1) if m else None


def _extract_session_id(thread_id: Optional[str], body: str) -> Optional[str]:
    if thread_id:
        return thread_id
    m = re.search(r"thread_id=([0-9a-fA-F-]{36})", body)
    return m.group(1) if m else None


def _find_last_user_prompt(request: dict[str, Any]) -> Optional[str]:
    inp = request.get("input")
    if isinstance(inp, str):
        return inp.strip() if inp.strip() else None
    if isinstance(inp, list):
        for item in reversed(inp):
            if not isinstance(item, dict):
                continue
            if item.get("type") != "input_text":
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return None


@dataclass
class PendingCall:
    item_id: str
    name: str
    call_id: Optional[str]
    created_id: int
    arguments: Optional[str] = None


class Bridge:
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.last_id = 0
        self.pending: dict[str, PendingCall] = {}
        self._load_state()

    def log(self, msg: str) -> None:
        if self.debug:
            sys.stderr.write(msg.rstrip() + "\n")
            sys.stderr.flush()

    def _load_state(self) -> None:
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.last_id = int(data.get("last_id") or 0)
        except Exception:
            self.last_id = 0

    def _save_state(self) -> None:
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            tmp = STATE_PATH.with_suffix(".tmp")
            tmp.write_text(json.dumps({"last_id": self.last_id}), encoding="utf-8")
            tmp.replace(STATE_PATH)
        except Exception:
            pass

    def _get_app_server_pid(self) -> Optional[int]:
        try:
            out = subprocess.check_output(CODEX_APPSERVER_PGREP, text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                line = line.strip()
                if line.isdigit():
                    return int(line)
        except Exception:
            pass

        try:
            out = subprocess.check_output(CODEX_APPSERVER_PS, text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "Codex.app/Contents/Resources/codex app-server" not in line:
                    continue
                m = re.match(r"\s*(\d+)\s+", line)
                if m:
                    return int(m.group(1))
        except Exception:
            pass
        return None

    def _open_db(self) -> sqlite3.Connection:
        uri = f"file:{CODEX_LOG_DB.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA busy_timeout=200;")
        return conn

    def _emit(self, payload: dict[str, Any]) -> None:
        if not BRIDGE.exists():
            return
        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8", errors="replace")
        try:
            subprocess.run(
                [str(BRIDGE), "--source", "codex"],
                input=data,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2,
                check=False,
                env=os.environ.copy(),
            )
        except Exception:
            pass

    def _emit_prompt(self, *, session_id: str, turn_id: Optional[str], cwd: Optional[str], model: Optional[str], prompt: str) -> None:
        self._emit(
            {
                "session_id": session_id,
                "turn_id": turn_id or "",
                "transcript_path": "",
                "cwd": cwd or "",
                "hook_event_name": "UserPromptSubmit",
                "model": model or "",
                "permission_mode": "unknown",
                "prompt": prompt,
            }
        )

    def _emit_pre(self, *, session_id: str, turn_id: Optional[str], cwd: Optional[str], tool_name: str, tool_input: Any, tool_use_id: str) -> None:
        self._emit(
            {
                "session_id": session_id,
                "turn_id": turn_id or "",
                "transcript_path": "",
                "cwd": cwd or "",
                "hook_event_name": "PreToolUse",
                "model": "",
                "permission_mode": "unknown",
                "tool_name": tool_name,
                "tool_input": tool_input if tool_input is not None else {},
                "tool_use_id": tool_use_id,
            }
        )

    def _emit_post(self, *, session_id: str, turn_id: Optional[str], cwd: Optional[str], tool_name: str, tool_input: Any, tool_use_id: str) -> None:
        self._emit(
            {
                "session_id": session_id,
                "turn_id": turn_id or "",
                "transcript_path": "",
                "cwd": cwd or "",
                "hook_event_name": "PostToolUse",
                "model": "",
                "permission_mode": "unknown",
                "tool_name": tool_name,
                "tool_input": tool_input if tool_input is not None else {},
                "tool_response": "",
                "tool_use_id": tool_use_id,
            }
        )

    def _handle_request_create(self, thread_id: Optional[str], body: str) -> None:
        req = _extract_json_after_marker(body, "websocket request: ")
        if not req or req.get("type") != "response.create":
            return
        prompt = _find_last_user_prompt(req)
        if not prompt:
            return
        session_id = _extract_session_id(thread_id, body)
        if not session_id:
            return
        self._emit_prompt(
            session_id=session_id,
            turn_id=_extract_turn_id(body),
            cwd=_extract_cwd(body),
            model=req.get("model") if isinstance(req.get("model"), str) else None,
            prompt=prompt,
        )

    def _handle_ws(self, thread_id: Optional[str], body: str) -> None:
        evt = _extract_json_after_marker(body, "websocket event: ")
        if evt is None:
            evt = _extract_json_after_marker(body, "Received message ")
        if evt is None:
            return

        session_id = _extract_session_id(thread_id, body)
        if not session_id:
            return
        turn_id = _extract_turn_id(body)
        cwd = _extract_cwd(body)

        et = evt.get("type")
        if not isinstance(et, str):
            return

        if et == "response.output_item.added":
            item = evt.get("item")
            if not isinstance(item, dict) or item.get("type") != "function_call":
                return
            item_id = item.get("id")
            name = item.get("name")
            call_id = item.get("call_id")
            if isinstance(item_id, str) and isinstance(name, str):
                self.pending[item_id] = PendingCall(
                    item_id=item_id,
                    name=name,
                    call_id=call_id if isinstance(call_id, str) else None,
                    created_id=self.last_id,
                )
            return

        if et == "response.function_call_arguments.done":
            item_id = evt.get("item_id")
            args = evt.get("arguments")
            if not isinstance(item_id, str) or not isinstance(args, str):
                return
            p = self.pending.get(item_id)
            if not p:
                self.pending[item_id] = PendingCall(item_id=item_id, name="unknown", call_id=None, created_id=self.last_id, arguments=args)
                p = self.pending[item_id]
            else:
                p.arguments = args

            tool_input = _safe_json_loads(args) or {"arguments": args}
            tool_use_id = p.call_id or item_id
            self._emit_pre(session_id=session_id, turn_id=turn_id, cwd=cwd, tool_name=p.name, tool_input=tool_input, tool_use_id=tool_use_id)
            return

        if et == "response.output_item.done":
            item = evt.get("item")
            if not isinstance(item, dict) or item.get("type") != "function_call":
                return
            item_id = item.get("id")
            name = item.get("name")
            call_id = item.get("call_id")
            args = item.get("arguments")
            if not isinstance(item_id, str) or not isinstance(name, str):
                return
            p = self.pending.get(item_id)
            if not p:
                p = PendingCall(item_id=item_id, name=name, call_id=call_id if isinstance(call_id, str) else None, created_id=self.last_id)
                self.pending[item_id] = p
            p.name = name
            if isinstance(call_id, str):
                p.call_id = call_id
            if isinstance(args, str) and args:
                p.arguments = args

            tool_input = _safe_json_loads(p.arguments) if isinstance(p.arguments, str) else None
            tool_input = tool_input if tool_input is not None else ({"arguments": p.arguments} if p.arguments else {})
            tool_use_id = p.call_id or item_id
            self._emit_post(session_id=session_id, turn_id=turn_id, cwd=cwd, tool_name=p.name, tool_input=tool_input, tool_use_id=tool_use_id)
            self.pending.pop(item_id, None)
            return

    def tick_once(self) -> None:
        pid = self._get_app_server_pid()
        if pid is None:
            time.sleep(1.0)
            return
        if not CODEX_LOG_DB.exists():
            time.sleep(1.0)
            return
        prefix = f"pid:{pid}:"

        try:
            conn = self._open_db()
            cur = conn.execute(
                "select id, thread_id, feedback_log_body from logs "
                "where id > ? and process_uuid like ? and feedback_log_body is not null "
                "order by id asc limit 500",
                (self.last_id, prefix + "%"),
            )
            rows = cur.fetchall()
        except Exception:
            rows = []
        finally:
            try:
                conn.close()
            except Exception:
                pass

        if not rows:
            time.sleep(0.2)
            return

        for rid, thread_id, body in rows:
            if isinstance(rid, int):
                self.last_id = max(self.last_id, rid)
            if not isinstance(body, str):
                continue
            th = thread_id if isinstance(thread_id, str) else None
            if "websocket request:" in body:
                self._handle_request_create(th, body)
            if ("websocket event:" in body) or body.startswith("Received message "):
                self._handle_ws(th, body)
        self._save_state()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args(argv)

    b = Bridge(debug=args.debug)
    if args.once:
        b.tick_once()
        return 0
    while True:
        b.tick_once()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

