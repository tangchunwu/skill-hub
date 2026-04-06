#!/usr/bin/env bash
set -euo pipefail

SERVER_ALIAS="openclaw-main"
SSH_SKILL_DIR=""

usage() {
  cat <<'EOF'
Usage:
  blinko_via_openclaw_server.sh healthcheck [--server openclaw-main]
  blinko_via_openclaw_server.sh classify --content-file /path/to/file [--server openclaw-main]
  blinko_via_openclaw_server.sh capture --content-file /path/to/file --confirmed [--mode auto|blinko|note|todo] [--source-ref URL] [--tags "#a #b"] [--server openclaw-main]
EOF
}

run_remote() {
  python3 "${SSH_SKILL_DIR}/ssh_execute.py" "$SERVER_ALIAS" "$1"
}

upload_then_remote() {
  local local_file="$1"
  local remote_file="$2"
  local remote_cmd="$3"
  python3 "${SSH_SKILL_DIR}/ssh_upload.py" "$SERVER_ALIAS" "$local_file" "$remote_file" --no-progress >/tmp/blinko_upload.json
  run_remote "$remote_cmd"
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

CMD="${1:-}"
[[ -n "$CMD" ]] || { usage; exit 64; }
shift || true

CONTENT_FILE=""
CONFIRMED="0"
MODE="auto"
SOURCE_REF=""
TAGS=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server) SERVER_ALIAS="${2:-}"; shift 2 ;;
    --content-file) CONTENT_FILE="${2:-}"; shift 2 ;;
    --confirmed) CONFIRMED="1"; shift ;;
    --mode) MODE="${2:-}"; shift 2 ;;
    --source-ref) SOURCE_REF="${2:-}"; shift 2 ;;
    --tags) TAGS="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[ERROR] unknown arg: $1" >&2; usage; exit 64 ;;
  esac
done

case "$CMD" in
  healthcheck)
    run_remote "bash /root/clawd/scripts/safe_blinko_skill.sh healthcheck"
    ;;
  classify)
    [[ -n "$CONTENT_FILE" && -f "$CONTENT_FILE" ]] || { echo "[ERROR] valid --content-file required" >&2; exit 64; }
    REMOTE_FILE="/tmp/blinko_classify_$(date +%s).txt"
    upload_then_remote "$CONTENT_FILE" "$REMOTE_FILE" "bash /root/clawd/scripts/safe_blinko_router.sh classify --content-file '$REMOTE_FILE'"
    ;;
  capture)
    [[ -n "$CONTENT_FILE" && -f "$CONTENT_FILE" ]] || { echo "[ERROR] valid --content-file required" >&2; exit 64; }
    [[ "$CONFIRMED" == "1" ]] || { echo "[ERROR] explicit confirmation required: pass --confirmed" >&2; exit 64; }
    REMOTE_FILE="/tmp/blinko_capture_$(date +%s).txt"
    REMOTE_CMD="bash /root/clawd/scripts/safe_blinko_router.sh capture --content-file '$REMOTE_FILE' --confirmed --mode '$MODE'"
    if [[ -n "$SOURCE_REF" ]]; then
      REMOTE_CMD+=" --source-ref '$SOURCE_REF'"
    fi
    if [[ -n "$TAGS" ]]; then
      REMOTE_CMD+=" --tags '$TAGS'"
    fi
    upload_then_remote "$CONTENT_FILE" "$REMOTE_FILE" "$REMOTE_CMD"
    ;;
  *)
    usage
    exit 64
    ;;
esac
