#!/usr/bin/env bash
set -euo pipefail

SERVER_ALIAS="openclaw-main"
SSH_SKILL_DIR=""
FILE_PATH=""

usage() {
  cat <<'EOF'
Usage:
  upload_via_openclaw_server.sh healthcheck [--server openclaw-main]
  upload_via_openclaw_server.sh upload --file /path/to/image.jpg [--server openclaw-main]
EOF
}

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

run_remote() {
  python3 "${SSH_SKILL_DIR}/ssh_execute.py" "$SERVER_ALIAS" "$1"
}

upload_then_remote() {
  local local_file="$1"
  local remote_file="$2"
  local remote_cmd="$3"
  python3 "${SSH_SKILL_DIR}/ssh_upload.py" "$SERVER_ALIAS" "$local_file" "$remote_file" --no-progress >/tmp/imagebed_upload.json
  run_remote "$remote_cmd"
}

CMD="${1:-}"
[[ -n "$CMD" ]] || { usage; exit 64; }
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server) SERVER_ALIAS="${2:-}"; shift 2 ;;
    --file) FILE_PATH="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERROR] unknown arg: $1" >&2; usage; exit 64 ;;
  esac
done

case "$CMD" in
  healthcheck)
    run_remote "python3 - <<'PY'
from pathlib import Path
for p in [
    '/root/clawd/scripts/test_morning_brief_upload.sh',
    '/root/clawd/scripts/telegram_image_mvp.sh',
    '/root/clawd/scripts/image_pipeline.sh',
]:
    if Path(p).exists():
        print('OK:', p)
        raise SystemExit(0)
raise SystemExit('image upload capability not found')
PY"
    ;;
  upload)
    [[ -n "$FILE_PATH" && -f "$FILE_PATH" ]] || { echo "[ERROR] valid --file required" >&2; exit 64; }
    REMOTE_FILE="/tmp/image_bed_$(date +%s)_$(basename "$FILE_PATH")"
    upload_then_remote "$FILE_PATH" "$REMOTE_FILE" "python3 - <<'PY'
import re
import subprocess
from pathlib import Path

image_path = Path('${REMOTE_FILE}')
if not image_path.exists():
    raise SystemExit(f'missing uploaded image: {image_path}')

script_candidates = [
    '/root/clawd/scripts/test_morning_brief_upload.sh',
    '/root/clawd/scripts/image_pipeline.sh',
    '/root/clawd/scripts/telegram_image_mvp.sh',
]

text = ''
for p in script_candidates:
    path = Path(p)
    if path.exists():
        text += '\\n' + path.read_text(encoding='utf-8', errors='ignore')

def pick(pattern, default=''):
    m = re.search(pattern, text)
    return m.group(1) if m else default

upload_url = pick(r'UPLOAD_URL=\"([^\"]+)\"', 'https://openclaw-tu.us.ci/upload')
upload_base = pick(r'UPLOAD_BASE_URL=\"([^\"]+)\"', 'https://openclaw-tu.us.ci')
field_name = pick(r'UPLOAD_FIELD_NAME=\"([^\"]+)\"', 'file')
bearer = pick(r'UPLOAD_AUTH_BEARER=\"([^\"]+)\"', '')

cmd = ['curl', '-sS', '-X', 'POST', upload_url]
if bearer:
    cmd += ['-H', f'Authorization: Bearer {bearer}']
cmd += ['-F', f'{field_name}=@{image_path}']

proc = subprocess.run(cmd, capture_output=True, text=True)
if proc.returncode != 0:
    print(proc.stderr, end='')
    raise SystemExit(proc.returncode)

resp = proc.stdout
m = re.search(r'\"src\"\\s*:\\s*\"([^\"]+)\"', resp)
if not m:
    print(resp)
    raise SystemExit('upload response missing src')

src = m.group(1)
if src.startswith('http://') or src.startswith('https://'):
    print(src)
else:
    print(upload_base + src)
PY"
    ;;
  *)
    usage
    exit 64
    ;;
esac
