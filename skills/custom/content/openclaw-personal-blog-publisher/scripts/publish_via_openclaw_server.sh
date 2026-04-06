#!/usr/bin/env bash
set -euo pipefail

JSON_FILE=""
SERVER_ALIAS="openclaw-main"
SSH_SKILL_DIR=""

usage() {
  cat <<'EOF'
Usage:
  publish_via_openclaw_server.sh --json-file /path/to/blog.json [--server openclaw-main]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json-file) JSON_FILE="${2:-}"; shift 2 ;;
    --server) SERVER_ALIAS="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERROR] unknown arg: $1" >&2; usage; exit 64 ;;
  esac
done

[[ -n "$JSON_FILE" && -f "$JSON_FILE" ]] || { echo "[ERROR] valid --json-file required" >&2; exit 64; }

for candidate in \
  "${HOME}/.codex/skills/ssh-skill/scripts" \
  "${HOME}/.claude/skills/ssh-skill/scripts"
do
  if [[ -f "${candidate}/ssh_execute.py" && -f "${candidate}/ssh_upload.py" ]]; then
    SSH_SKILL_DIR="$candidate"
    break
  fi
done

[[ -n "$SSH_SKILL_DIR" ]] || { echo "[ERROR] ssh skill scripts not found in ~/.codex or ~/.claude" >&2; exit 2; }

REMOTE_JSON="/tmp/blog_publish_$(date +%s).json"

python3 "${SSH_SKILL_DIR}/ssh_upload.py" "$SERVER_ALIAS" "$JSON_FILE" "$REMOTE_JSON" --no-progress >/tmp/blog_publish_upload.json

python3 "${SSH_SKILL_DIR}/ssh_execute.py" "$SERVER_ALIAS" "python3 - <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

payload_path = Path('${REMOTE_JSON}')
skill_path = Path('/root/clawd/skills/personal-blog-publisher/SKILL.md')
payload = payload_path.read_text(encoding='utf-8')
text = skill_path.read_text(encoding='utf-8')

url_match = re.search(r'POST\\s+(https://\\S+)', text)
token_match = re.search(r'Authorization:\\s+Bearer\\s+(\\S+)', text)
if not url_match or not token_match:
    raise SystemExit('missing blog publish endpoint or token in server skill')

url = url_match.group(1)
token = token_match.group(1)
url = url.replace(chr(96), '').replace(\"'\", '').replace('\"', '')
token = token.replace(chr(96), '').replace(\"'\", '').replace('\"', '')
proc = subprocess.run(
    [
        'curl', '-sS', '-X', 'POST', url,
        '-H', 'Content-Type: application/json',
        '-H', f'Authorization: Bearer {token}',
        '-d', payload,
    ],
    capture_output=True,
    text=True,
)
print(proc.stdout)
if proc.returncode != 0:
    print(proc.stderr, file=sys.stderr)
    raise SystemExit(proc.returncode)
PY"
