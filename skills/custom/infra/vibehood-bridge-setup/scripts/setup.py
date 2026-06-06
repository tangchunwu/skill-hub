#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import time
import tempfile
from pathlib import Path
from typing import Any, Optional


HOME = Path.home()
GEMINI_HOOK_TIMEOUT_MS = 5000
CLAUDE_HOOK_TIMEOUT_S = 5

VIBEHOOD_DIR = HOME / ".vibehood"
VIBEHOOD_BIN = VIBEHOOD_DIR / "bin"
VIBEHOOD_LOGS = VIBEHOOD_DIR / "logs"
VIBEHOOD_STATE = VIBEHOOD_DIR / "state"

CODEX_DIR = HOME / ".codex"
CODEX_HOOKS = CODEX_DIR / "hooks.json"
CODEX_LOG_DB = CODEX_DIR / "logs_2.sqlite"

GEMINI_DIR = HOME / ".gemini"
GEMINI_SETTINGS = GEMINI_DIR / "settings.json"

CLAUDE_DIR = HOME / ".claude"
CLAUDE_HOOKS = CLAUDE_DIR / "hooks" / "hooks.json"
CLAUDE_SETTINGS = CLAUDE_DIR / "settings.json"
CLAUDE_SETTINGS_LOCAL = CLAUDE_DIR / "settings.local.json"

LAUNCH_AGENTS = HOME / "Library" / "LaunchAgents"
PLIST_PATH = LAUNCH_AGENTS / "com.vibehood.codex-desktop-bridge.plist"


def die(msg: str, code: int = 1) -> None:
    sys.stderr.write(msg.rstrip() + "\n")
    raise SystemExit(code)


def now_ts() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def backup_file(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    bak = path.with_suffix(path.suffix + f".bak-{now_ts()}")
    try:
        shutil.copy2(path, bak)
        return bak
    except Exception:
        return None


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def chmod_x(path: Path) -> None:
    st = path.stat()
    path.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def which(exe: str) -> Optional[str]:
    try:
        out = subprocess.check_output(["/usr/bin/which", exe], text=True).strip()
        return out if out else None
    except Exception:
        return None


def ensure_vibehood_bridge() -> Path:
    bridge = VIBEHOOD_BIN / "vibehood-bridge"
    if bridge.exists():
        return bridge
    # fallback: search PATH
    p = which("vibehood-bridge")
    if p:
        return Path(p)
    die(
        "Missing `vibehood-bridge`.\n"
        "Open VibeHood once so it installs `~/.vibehood/bin/vibehood-bridge`, then rerun this setup."
    )
    raise AssertionError("unreachable")


def write_gemini_hook(bridge: Path) -> Path:
    VIBEHOOD_BIN.mkdir(parents=True, exist_ok=True)
    hook_path = VIBEHOOD_BIN / "vibehood-bridge-gemini-hook"
    content = f"""#!/usr/bin/python3
import subprocess
import sys
import json
import time
from pathlib import Path

BRIDGE = str(Path.home() / ".vibehood" / "bin" / "vibehood-bridge")
LOG_PATH = Path.home() / ".vibehood" / "logs" / "hook-compat.log"
SPOOL_DIR = Path.home() / ".vibehood" / "state" / "claude-hook-spool"

EVENT_MAP = {{
    "SessionStart": "sessionStart",
    "BeforeAgent": "beforeSubmitPrompt",
    "AfterAgent": "sessionEnd",
    "SessionEnd": "sessionEnd",
    "PreCompress": "pre_compact",
    "UserPromptSubmit": "user_prompt_submit",
}}

SHELL_TOOLS = {{"run_shell_command"}}
READ_TOOLS = {{"read_file", "glob", "grep", "ls"}}
WRITE_TOOLS = {{"write_file", "replace"}}
MCP_TOOLS = {{"mcp"}}


def append_log(message: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(message + "\\n")
    except Exception:
        pass


def normalize_payload(payload_bytes: bytes) -> bytes:
    if not payload_bytes:
        payload_bytes = b"{{}}\\n"
    try:
        data = json.loads(payload_bytes.decode("utf-8", "ignore"))
        if not isinstance(data, dict):
            return payload_bytes
    except Exception:
        append_log(f"{{time.time():.3f}} gemini invalid-json")
        return payload_bytes

    original_event = data.get("hook_event_name")
    tool_name = data.get("tool_name")
    mapped_event = original_event if isinstance(original_event, str) else None
    if isinstance(original_event, str):
        mapped_event = EVENT_MAP.get(original_event, original_event)
        if original_event == "BeforeTool" and isinstance(tool_name, str):
            if tool_name in SHELL_TOOLS:
                mapped_event = "beforeShellExecution"
            elif tool_name in READ_TOOLS:
                mapped_event = "beforeReadFile"
            elif tool_name in MCP_TOOLS:
                mapped_event = "beforeMCPExecution"
        elif original_event == "AfterTool" and isinstance(tool_name, str):
            if tool_name in SHELL_TOOLS:
                mapped_event = "afterShellExecution"
            elif tool_name in WRITE_TOOLS:
                mapped_event = "afterFileEdit"
            elif tool_name in MCP_TOOLS:
                mapped_event = "afterMCPExecution"
        data["hook_event_name"] = mapped_event
        data["event"] = mapped_event

    # Bridge v0.3.0 only advertises claude/cursor sources. Gemini uses claude compatibility mode.
    if "prompt" not in data and isinstance(data.get("user_input"), str):
        data["prompt"] = data["user_input"]

    append_log(
        f"{{time.time():.3f}} gemini event={{original_event!r}} mapped={{mapped_event!r}} keys={{sorted(data.keys())}}"
    )
    return (json.dumps(data, ensure_ascii=False) + "\\n").encode("utf-8")


def read_stdin_nonblocking() -> bytes:
    \"\"\"Read stdin if Gemini provides it, but don't hang if it doesn't.\"\"\"
    try:
        fd = sys.stdin.fileno()
    except Exception:
        return b""

    try:
        import os
        import fcntl
        import select
        import time

        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        ready, _, _ = select.select([fd], [], [], 0.2)
        if not ready:
            return b""
    except Exception:
        return b""

    chunks = []
    idle_deadline = time.monotonic() + 1.0
    while True:
        if time.monotonic() > idle_deadline:
            break
        try:
            ready, _, _ = select.select([fd], [], [], 0.05)
        except Exception:
            break
        if not ready:
            break
        try:
            data = os.read(fd, 65536)
        except BlockingIOError:
            continue
        except Exception:
            break
        if not data:
            break
        chunks.append(data)
    return b"".join(chunks)


payload = read_stdin_nonblocking()
out_payload = normalize_payload(payload)

try:
    result = subprocess.run(
        [BRIDGE, "--source", "claude"],
        input=out_payload,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout={CLAUDE_HOOK_TIMEOUT_S},
        check=False,
    )
    append_log(f"{{time.time():.3f}} gemini rc={{result.returncode}}")
except Exception as exc:
    append_log(f"{{time.time():.3f}} gemini exception={{exc!r}}")

sys.stdout.buffer.write(out_payload)
"""
    hook_path.write_text(content, encoding="utf-8")
    chmod_x(hook_path)
    return hook_path


def write_claude_hook() -> Path:
    VIBEHOOD_BIN.mkdir(parents=True, exist_ok=True)
    hook_path = VIBEHOOD_BIN / "vibehood-bridge-claude-hook"
    content = """#!/usr/bin/python3
import subprocess
import sys
import json
import time
from pathlib import Path

BRIDGE = str(Path.home() / ".vibehood" / "bin" / "vibehood-bridge")
LOG_PATH = Path.home() / ".vibehood" / "logs" / "hook-compat.log"

EVENT_MAP = {
    "SessionStart": "sessionStart",
    "SessionEnd": "sessionEnd",
    "Stop": "sessionEnd",
    "UserPromptSubmit": "beforeSubmitPrompt",
    "PreCompact": "pre_compact",
}

SHELL_TOOLS = {"Bash", "Shell", "run_shell_command"}
READ_TOOLS = {"Read", "Glob", "Grep", "LS", "Search", "read_file", "glob", "grep", "ls"}
WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "replace", "write_file"}
MCP_TOOLS = {"MCP", "mcp", "Task"}


def append_log(message: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(message + "\\n")
    except Exception:
        pass


def normalize_payload(payload_bytes: bytes) -> bytes:
    if not payload_bytes:
        payload_bytes = b"{}\\n"
    try:
        data = json.loads(payload_bytes.decode("utf-8", "ignore"))
        if not isinstance(data, dict):
            return payload_bytes
    except Exception:
        append_log(f"{time.time():.3f} claude invalid-json")
        return payload_bytes

    original_event = data.get("hook_event_name")
    tool_name = data.get("tool_name")
    if not isinstance(tool_name, str):
        tool_name = data.get("tool")
    mapped_event = original_event if isinstance(original_event, str) else None
    if isinstance(original_event, str):
        mapped_event = EVENT_MAP.get(original_event, original_event)
        if original_event == "PreToolUse" and isinstance(tool_name, str):
            if tool_name in SHELL_TOOLS:
                mapped_event = "beforeShellExecution"
            elif tool_name in READ_TOOLS:
                mapped_event = "beforeReadFile"
            elif tool_name in MCP_TOOLS:
                mapped_event = "beforeMCPExecution"
        elif original_event == "PostToolUse" and isinstance(tool_name, str):
            if tool_name in SHELL_TOOLS:
                mapped_event = "afterShellExecution"
            elif tool_name in WRITE_TOOLS:
                mapped_event = "afterFileEdit"
            elif tool_name in MCP_TOOLS:
                mapped_event = "afterMCPExecution"
        data["hook_event_name"] = mapped_event
        data["event"] = mapped_event

    if "prompt" not in data and isinstance(data.get("user_input"), str):
        data["prompt"] = data["user_input"]

    append_log(
        f"{time.time():.3f} claude event={original_event!r} mapped={mapped_event!r} keys={sorted(data.keys())}"
    )
    return (json.dumps(data, ensure_ascii=False) + "\\n").encode("utf-8")

payload = sys.stdin.buffer.read()
out_payload = normalize_payload(payload)

try:
    SPOOL_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb", prefix="payload-", suffix=".json", dir=SPOOL_DIR, delete=False
    ) as fh:
        fh.write(out_payload)
        payload_path = fh.name

    worker = (
        "import pathlib, subprocess, sys, time; "
        "path=pathlib.Path(sys.argv[1]); bridge=sys.argv[2]; log=pathlib.Path(sys.argv[3]); "
        "rc='unknown'; "
        "\\ntry:\\n"
        "    data=path.read_bytes()\\n"
        "    result=subprocess.run([bridge, '--source', 'claude'], input=data, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30, check=False)\\n"
        "    rc=result.returncode\\n"
        "except Exception as exc:\\n"
        "    rc='exception=' + repr(exc)\\n"
        "finally:\\n"
        "    try:\\n"
        "        log.parent.mkdir(parents=True, exist_ok=True)\\n"
        "        with log.open('a', encoding='utf-8') as lf: lf.write(f'{time.time():.3f} claude bg rc={rc}\\\\n')\\n"
        "    except Exception: pass\\n"
        "    try: path.unlink()\\n"
        "    except Exception: pass\\n"
    )
    subprocess.Popen(
        [sys.executable, "-c", worker, payload_path, BRIDGE, str(LOG_PATH)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    append_log(f"{time.time():.3f} claude queued={Path(payload_path).name}")
except Exception as exc:
    append_log(f"{time.time():.3f} claude exception={exc!r}")

sys.stdout.buffer.write(out_payload)
"""
    content = content.replace("__CLAUDE_TIMEOUT__", str(CLAUDE_HOOK_TIMEOUT_S))
    hook_path.write_text(content, encoding="utf-8")
    chmod_x(hook_path)
    return hook_path


def seed_codex_desktop_state(pid: Optional[int]) -> int:
    if not CODEX_LOG_DB.exists():
        return 0
    try:
        uri = f"file:{CODEX_LOG_DB.as_posix()}?mode=ro"
        conn = sqlite3_connect(uri)
        try:
            if pid:
                prefix = f"pid:{pid}:%"
                row = conn.execute(
                    "select max(id) from logs where process_uuid like ?",
                    (prefix,),
                ).fetchone()
            else:
                row = conn.execute("select max(id) from logs").fetchone()
            v = int(row[0] or 0) if row else 0
            return v
        finally:
            conn.close()
    except Exception:
        return 0


def sqlite3_connect(uri: str):
    import sqlite3

    conn = sqlite3.connect(uri, uri=True)
    conn.execute("PRAGMA busy_timeout=200;")
    return conn


def find_codex_app_server_pid() -> Optional[int]:
    # Prefer ps scanning (more reliable on macOS than pgrep -f in some setups)
    try:
        out = subprocess.check_output(["ps", "ax", "-o", "pid=,command="], text=True)
        for line in out.splitlines():
            if "Codex.app/Contents/Resources/codex app-server" not in line:
                continue
            parts = line.strip().split(" ", 1)
            if parts and parts[0].isdigit():
                return int(parts[0])
    except Exception:
        return None
    return None


def write_codex_desktop_bridge(bridge: Path) -> Path:
    VIBEHOOD_BIN.mkdir(parents=True, exist_ok=True)
    path = VIBEHOOD_BIN / "vibehood-bridge-codex-desktop"
    src = Path(__file__).resolve().parent / "vibehood-bridge-codex-desktop.py"
    if not src.exists():
        die(f"Missing skill resource: {src}")
    path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    chmod_x(path)
    return path


def ensure_gemini_settings(hook_cmd: str) -> None:
    GEMINI_DIR.mkdir(parents=True, exist_ok=True)
    backup_file(GEMINI_SETTINGS)
    data = read_json(GEMINI_SETTINGS)

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks

    def strip_command_hooks(event: str) -> list[dict[str, Any]]:
        rules = hooks.get(event)
        if not isinstance(rules, list):
            rules = []
        cleaned_rules: list[dict[str, Any]] = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            hs = rule.get("hooks")
            if not isinstance(hs, list):
                cleaned_rules.append(rule)
                continue
            kept_hooks = [
                h
                for h in hs
                if not (
                    isinstance(h, dict)
                    and h.get("type") == "command"
                    and h.get("command") == hook_cmd
                )
            ]
            if kept_hooks:
                new_rule = dict(rule)
                new_rule["hooks"] = kept_hooks
                cleaned_rules.append(new_rule)
        hooks[event] = cleaned_rules
        return cleaned_rules

    def ensure_event(event: str, *, matcher: Optional[str] = None) -> None:
        event_rules = hooks.get(event)
        if not isinstance(event_rules, list):
            event_rules = []
            hooks[event] = event_rules

        strip_command_hooks(event)
        event_rules = hooks.get(event)
        if not isinstance(event_rules, list):
            event_rules = []
            hooks[event] = event_rules

        # Not found: append a new rule.
        new_rule: dict[str, Any] = {
            "hooks": [{"type": "command", "command": hook_cmd, "timeout": GEMINI_HOOK_TIMEOUT_MS}]
        }
        if matcher is not None:
            new_rule["matcher"] = matcher
        event_rules.append(new_rule)

    ensure_event("SessionStart")
    ensure_event("BeforeAgent")
    ensure_event("AfterAgent")
    ensure_event("SessionEnd")
    ensure_event("PreCompress")

    # Limit tool hooks to common tool-like actions (same as current local setup).
    tool_matcher = "run_shell_command|replace|write_file|read_file|glob|grep|ls"
    ensure_event("BeforeTool", matcher=tool_matcher)
    ensure_event("AfterTool", matcher=tool_matcher)

    write_json(GEMINI_SETTINGS, data)


def ensure_codex_hooks(vibehood_bridge_cmd: str) -> None:
    CODEX_DIR.mkdir(parents=True, exist_ok=True)
    backup_file(CODEX_HOOKS)
    data = read_json(CODEX_HOOKS)

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks

    def strip_command_hooks(event: str) -> list[dict[str, Any]]:
        rules = hooks.get(event)
        if not isinstance(rules, list):
            rules = []
        cleaned_rules: list[dict[str, Any]] = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            hs = rule.get("hooks")
            if not isinstance(hs, list):
                cleaned_rules.append(rule)
                continue
            kept_hooks = [
                h
                for h in hs
                if not (
                    isinstance(h, dict)
                    and h.get("type") == "command"
                    and h.get("command") == vibehood_bridge_cmd
                )
            ]
            if kept_hooks:
                new_rule = dict(rule)
                new_rule["hooks"] = kept_hooks
                cleaned_rules.append(new_rule)
        hooks[event] = cleaned_rules
        return cleaned_rules

    def ensure_hook(event: str, *, matcher: Optional[str], status: str, timeout: Optional[int] = None) -> None:
        rules = hooks.get(event)
        if not isinstance(rules, list):
            rules = []
            hooks[event] = rules

        strip_command_hooks(event)
        rules = hooks.get(event)
        if not isinstance(rules, list):
            rules = []
            hooks[event] = rules

        # Append new
        cmd: dict[str, Any] = {"type": "command", "command": vibehood_bridge_cmd}
        if status:
            cmd["statusMessage"] = status
        if timeout is not None:
            cmd["timeout"] = timeout
        new_rule: dict[str, Any] = {"hooks": [cmd]}
        if matcher is not None:
            new_rule["matcher"] = matcher
        rules.append(new_rule)

    ensure_hook(
        "SessionStart",
        matcher="startup|resume",
        status="Reporting VibeHood activity",
    )
    ensure_hook(
        "UserPromptSubmit",
        matcher=None,
        status="Reporting VibeHood prompt",
    )
    tool_matcher = "Bash|Edit|Write|Read|Glob|Grep|Task|WebFetch|WebSearch"
    ensure_hook(
        "PreToolUse",
        matcher=tool_matcher,
        status="Reporting VibeHood tool start",
    )
    ensure_hook(
        "PostToolUse",
        matcher=tool_matcher,
        status="Reporting VibeHood tool result",
    )
    ensure_hook(
        "Stop",
        matcher=None,
        status="",
        timeout=10,
    )

    write_json(CODEX_HOOKS, data)


def ensure_claude_hooks(hook_cmd: str) -> None:
    # Claude Code loads hooks from ~/.claude/hooks/hooks.json (if present).
    if not CLAUDE_HOOKS.exists():
        return

    backup_file(CLAUDE_HOOKS)
    data = read_json(CLAUDE_HOOKS)

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        data["hooks"] = hooks

    def strip_command_hooks(event: str) -> list[dict[str, Any]]:
        rules = hooks.get(event)
        if not isinstance(rules, list):
            rules = []
        cleaned_rules: list[dict[str, Any]] = []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            hs = rule.get("hooks")
            if not isinstance(hs, list):
                cleaned_rules.append(rule)
                continue
            kept_hooks = [
                h
                for h in hs
                if not (
                    isinstance(h, dict)
                    and h.get("type") == "command"
                    and h.get("command") == hook_cmd
                )
            ]
            if kept_hooks:
                new_rule = dict(rule)
                new_rule["hooks"] = kept_hooks
                cleaned_rules.append(new_rule)
        hooks[event] = cleaned_rules
        return cleaned_rules

    def ensure_event(event: str) -> None:
        rules = hooks.get(event)
        if not isinstance(rules, list):
            rules = []
            hooks[event] = rules

        strip_command_hooks(event)
        rules = hooks.get(event)
        if not isinstance(rules, list):
            rules = []
            hooks[event] = rules

        rules.append(
            {
                "matcher": "*",
                "hooks": [{"type": "command", "command": hook_cmd, "timeout": CLAUDE_HOOK_TIMEOUT_S, "async": True}],
                "description": "Report Claude Code activity to VibeHood",
                "id": f"vibehood:report:{event.lower()}",
            }
        )

    for ev in ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PreCompact", "Stop", "SessionEnd"]:
        ensure_event(ev)

    write_json(CLAUDE_HOOKS, data)


def ensure_claude_settings_hooks(hook_cmd: str) -> None:
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)

    def update_settings_file(path: Path) -> None:
        backup_file(path)
        data = read_json(path)

        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            hooks = {}
            data["hooks"] = hooks

        def strip_command_hooks(event: str) -> None:
            rules = hooks.get(event)
            if not isinstance(rules, list):
                hooks[event] = []
                return
            cleaned_rules: list[dict[str, Any]] = []
            for rule in rules:
                if not isinstance(rule, dict):
                    continue
                hs = rule.get("hooks")
                if not isinstance(hs, list):
                    cleaned_rules.append(rule)
                    continue
                kept_hooks = [
                    h
                    for h in hs
                    if not (
                        isinstance(h, dict)
                        and h.get("type") == "command"
                        and h.get("command") == hook_cmd
                    )
                ]
                if kept_hooks:
                    new_rule = dict(rule)
                    new_rule["hooks"] = kept_hooks
                    cleaned_rules.append(new_rule)
            hooks[event] = cleaned_rules

        def ensure_event(event: str) -> None:
            rules = hooks.get(event)
            if not isinstance(rules, list):
                rules = []
                hooks[event] = rules

            strip_command_hooks(event)
            rules = hooks.get(event)
            if not isinstance(rules, list):
                rules = []
                hooks[event] = rules

            rules.append(
                {
                    "matcher": "*",
                    "hooks": [{"type": "command", "command": hook_cmd, "timeout": 2, "async": True}],
                }
            )

        for ev in ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PreCompact", "Stop", "SessionEnd"]:
            ensure_event(ev)

        write_json(path, data)

    update_settings_file(CLAUDE_SETTINGS)
    update_settings_file(CLAUDE_SETTINGS_LOCAL)


def write_launch_agent() -> None:
    LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)
    VIBEHOOD_LOGS.mkdir(parents=True, exist_ok=True)

    out_log = (VIBEHOOD_LOGS / "codex-desktop-bridge.out.log").as_posix()
    err_log = (VIBEHOOD_LOGS / "codex-desktop-bridge.err.log").as_posix()
    script = (VIBEHOOD_BIN / "vibehood-bridge-codex-desktop").as_posix()

    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.vibehood.codex-desktop-bridge</string>

    <key>ProgramArguments</key>
    <array>
      <string>/usr/bin/python3</string>
      <string>{script}</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>{out_log}</string>
    <key>StandardErrorPath</key>
    <string>{err_log}</string>
  </dict>
</plist>
"""
    backup_file(PLIST_PATH)
    PLIST_PATH.write_text(content, encoding="utf-8")


def launchctl_load() -> None:
    # Best-effort. Replace the running job so plist/script updates apply immediately.
    try:
        uid = os.getuid()
        service = f"gui/{uid}/com.vibehood.codex-desktop-bridge"
        subprocess.run(
            ["launchctl", "bootout", f"gui/{uid}", str(PLIST_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        subprocess.run(
            ["launchctl", "bootstrap", f"gui/{uid}", str(PLIST_PATH)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        subprocess.run(
            ["launchctl", "enable", service],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        subprocess.run(
            ["launchctl", "kickstart", "-k", service],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except Exception:
        try:
            subprocess.run(
                ["launchctl", "load", "-w", str(PLIST_PATH)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass


def main() -> int:
    bridge_bin = ensure_vibehood_bridge()
    VIBEHOOD_BIN.mkdir(parents=True, exist_ok=True)

    gemini_hook = write_gemini_hook(bridge_bin)
    claude_hook = write_claude_hook()
    codex_desktop_bridge = write_codex_desktop_bridge(bridge_bin)

    # Seed state to "now" to avoid replaying old history.
    VIBEHOOD_STATE.mkdir(parents=True, exist_ok=True)
    pid = find_codex_app_server_pid()
    last_id = seed_codex_desktop_state(pid)
    (VIBEHOOD_STATE / "codex-desktop-bridge.json").write_text(json.dumps({"last_id": last_id}) + "\n", encoding="utf-8")

    ensure_gemini_settings(str(gemini_hook))
    ensure_codex_hooks(f"{bridge_bin.as_posix()} --source codex")
    ensure_claude_hooks(str(claude_hook))
    ensure_claude_settings_hooks(str(claude_hook))

    write_launch_agent()
    launchctl_load()

    sys.stdout.write("VibeHood bridge setup complete.\n")
    sys.stdout.write(f"- Gemini hook: {gemini_hook}\n")
    sys.stdout.write(f"- Claude hook: {claude_hook}\n")
    sys.stdout.write(f"- Codex Desktop bridge: {codex_desktop_bridge}\n")
    sys.stdout.write(f"- LaunchAgent: {PLIST_PATH}\n")
    sys.stdout.write(f"- Seeded state last_id={last_id}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
