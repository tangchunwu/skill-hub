#!/usr/bin/env bash
set -euo pipefail

PUBLIC_BASE=""
ENV_FILE="${OPENCLAW_GATEWAY_ENV_FILE:-/root/.config/openclaw/gateway.env}"
CONFIG_FILE="${OPENCLAW_CONFIG_FILE:-/root/.openclaw/openclaw.json}"
OUTPUT_JSON="false"
TARGET="${OPENCLAW_CHANNEL_TARGET:-auto}"
LOCAL_BASE="${OPENCLAW_LOCAL_BASE_URL:-}"
LOCAL_HOST="${OPENCLAW_LOCAL_HOST:-127.0.0.1}"
LOCAL_PORT="${OPENCLAW_LOCAL_PORT:-}"

usage() {
  cat <<'USAGE'
Usage:
  emit_channel_config.sh [--target MODE] [--public-base URL] [--local-base URL] [--env-file FILE] [--config FILE] [--json]

Options:
  --target MODE       auto|external|local (default: auto; prefer external when available)
  --public-base URL   Override Webhook URL base (e.g. https://ccnu.ccwu.cc)
  --local-base URL    Override local Webhook URL (e.g. http://127.0.0.1:18789)
  --env-file FILE     Gateway env file path (default: /root/.config/openclaw/gateway.env)
  --config FILE       OpenClaw config path (default: /root/.openclaw/openclaw.json)
  --json              Output JSON instead of plain text
USAGE
}

trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

strip_quotes() {
  local s="$1"
  if [[ "$s" =~ ^\".*\"$ ]]; then
    s="${s:1:${#s}-2}"
  elif [[ "$s" =~ ^\'.*\'$ ]]; then
    s="${s:1:${#s}-2}"
  fi
  printf '%s' "$s"
}

is_ascii_only() {
  local s="$1"
  local non_ascii
  non_ascii="$(LC_ALL=C printf '%s' "$s" | tr -d '\000-\177')"
  [[ -z "$non_ascii" ]]
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || { echo "missing value for --target" >&2; exit 2; }
      TARGET="$2"
      shift 2
      ;;
    --public-base)
      [[ $# -ge 2 ]] || { echo "missing value for --public-base" >&2; exit 2; }
      PUBLIC_BASE="$2"
      shift 2
      ;;
    --local-base)
      [[ $# -ge 2 ]] || { echo "missing value for --local-base" >&2; exit 2; }
      LOCAL_BASE="$2"
      shift 2
      ;;
    --env-file)
      [[ $# -ge 2 ]] || { echo "missing value for --env-file" >&2; exit 2; }
      ENV_FILE="$2"
      shift 2
      ;;
    --config)
      [[ $# -ge 2 ]] || { echo "missing value for --config" >&2; exit 2; }
      CONFIG_FILE="$2"
      shift 2
      ;;
    --json)
      OUTPUT_JSON="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown arg: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

TARGET="$(trim "$TARGET")"
TARGET="$(printf '%s' "$TARGET" | tr '[:upper:]' '[:lower:]')"
case "$TARGET" in
  auto|external|local) ;;
  *)
    echo "error: --target must be one of: auto, external, local" >&2
    exit 2
    ;;
esac

read_token_from_env_file() {
  local file="$1"
  [[ -f "$file" ]] || { printf ''; return 0; }
  local line raw
  line="$(grep -E '^[[:space:]]*OPENCLAW_GATEWAY_PASSWORD[[:space:]]*=' "$file" | tail -n 1 || true)"
  [[ -n "$line" ]] || { printf ''; return 0; }
  raw="${line#*=}"
  raw="$(trim "$raw")"
  strip_quotes "$raw"
}

read_json_field() {
  local file="$1"
  local expr="$2"
  [[ -f "$file" ]] || { printf ''; return 0; }
  jq -er "$expr // empty" "$file" 2>/dev/null || printf ''
}

detect_public_base_from_nginx() {
  local f="/etc/nginx/conf.d/openclaw_ccnu.conf"
  [[ -f "$f" ]] || return 1
  local host
  host="$(awk '/server_name/ {for (i=1;i<=NF;i++) if ($i=="server_name") {print $(i+1); exit}}' "$f" | sed 's/;//g')"
  [[ -n "$host" ]] || return 1
  printf 'https://%s' "$host"
}

is_localish_url() {
  local u="$1"
  [[ "$u" =~ ^https?://(localhost|127\.0\.0\.1|\[::1\]|0\.0\.0\.0)(:|/|$) ]]
}

detect_local_base() {
  local base host port
  base="$(trim "${LOCAL_BASE:-}")"
  if [[ -n "$base" ]]; then
    printf '%s' "$base"
    return 0
  fi

  base="$(trim "${OPENCLAW_LOCAL_BASE_URL:-}")"
  if [[ -n "$base" ]]; then
    printf '%s' "$base"
    return 0
  fi

  host="$(trim "${LOCAL_HOST:-127.0.0.1}")"
  port="$(trim "${LOCAL_PORT:-}")"
  if [[ -z "$port" ]]; then
    port="$(read_json_field "$CONFIG_FILE" '.gateway.port')"
  fi
  if [[ -z "$port" ]]; then
    port="18789"
  fi
  printf 'http://%s:%s' "$host" "$port"
}

EXTERNAL_URL="$(trim "${PUBLIC_BASE:-}")"
if [[ -z "$EXTERNAL_URL" ]]; then
  EXTERNAL_URL="$(trim "${OPENCLAW_PUBLIC_BASE_URL:-}")"
fi
if [[ -z "$EXTERNAL_URL" ]]; then
  EXTERNAL_URL="$(trim "${OPENCLAW_WEBHOOK_URL:-}")"
fi
if [[ -z "$EXTERNAL_URL" ]]; then
  EXTERNAL_URL="$(read_json_field "$CONFIG_FILE" '.gateway.publicBaseUrl')"
fi
if [[ -z "$EXTERNAL_URL" ]]; then
  EXTERNAL_URL="$(read_json_field "$CONFIG_FILE" '.gateway.publicUrl')"
fi
if [[ -z "$EXTERNAL_URL" ]]; then
  EXTERNAL_URL="$(detect_public_base_from_nginx || true)"
fi

TOKEN="$(trim "${OPENCLAW_GATEWAY_PASSWORD:-}")"
if [[ -z "$TOKEN" ]]; then
  TOKEN="$(read_token_from_env_file "$ENV_FILE" || true)"
fi
if [[ -z "$TOKEN" ]]; then
  TOKEN="$(read_json_field "$CONFIG_FILE" '.gateway.auth.password' || true)"
fi

EXTERNAL_URL="${EXTERNAL_URL%/}"
LOCAL_URL="$(detect_local_base)"
LOCAL_URL="${LOCAL_URL%/}"

WEBHOOK_URL=""
case "$TARGET" in
  external)
    WEBHOOK_URL="$EXTERNAL_URL"
    ;;
  local)
    WEBHOOK_URL="$LOCAL_URL"
    ;;
  auto)
    if [[ -n "$EXTERNAL_URL" ]] && ! is_localish_url "$EXTERNAL_URL"; then
      WEBHOOK_URL="$EXTERNAL_URL"
    else
      WEBHOOK_URL="$LOCAL_URL"
    fi
    ;;
esac

if [[ -z "$WEBHOOK_URL" ]]; then
  if [[ "$TARGET" == "external" ]]; then
    echo "error: external webhook URL not found; pass --public-base or set OPENCLAW_PUBLIC_BASE_URL" >&2
  else
    echo "error: webhook URL not found; pass --public-base/--local-base or set OPENCLAW_PUBLIC_BASE_URL" >&2
  fi
  exit 3
fi
if [[ ! "$WEBHOOK_URL" =~ ^https?:// ]]; then
  echo "error: webhook URL must start with http:// or https:// (got: $WEBHOOK_URL)" >&2
  exit 3
fi
if [[ -z "$TOKEN" ]]; then
  echo "error: token not found; check OPENCLAW_GATEWAY_PASSWORD or $ENV_FILE" >&2
  exit 4
fi
if ! is_ascii_only "$TOKEN"; then
  echo "error: token contains non-ASCII characters; verify full-width/Unicode input" >&2
  exit 5
fi

if [[ "$OUTPUT_JSON" == "true" ]]; then
  jq -n --arg webhook_url "$WEBHOOK_URL" --arg token "$TOKEN" \
    '{webhook_url:$webhook_url, token:$token}'
else
  printf 'Webhook URL: %s\n' "$WEBHOOK_URL"
  printf 'Token: %s\n' "$TOKEN"
fi
