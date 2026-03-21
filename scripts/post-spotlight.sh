#!/usr/bin/env bash
# post-spotlight.sh — run spotlight, upload HTML, post tweet via frigatebird
# Logs result to ~/.local/share/agentkit/spotlight-post-log.jsonl
#
# Usage:
#   ./post-spotlight.sh             — upload + post tweet (live)
#   ./post-spotlight.sh --dry-run   — print tweet text only, do NOT call frigatebird
set -euo pipefail

LOG_DIR="${HOME}/.local/share/agentkit"
LOG_FILE="${LOG_DIR}/spotlight-post-log.jsonl"
DATE_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DATE_SHORT="$(date -u +%Y-%m-%d)"

# Parse flags
DRY_RUN=0
TARGET=""
for arg in "$@"; do
    case "${arg}" in
        --dry-run) DRY_RUN=1 ;;
        --target=*) TARGET="${arg#--target=}" ;;
        --target) shift; TARGET="${1:-}" ;;
    esac
done

# If no --target, get from spotlight-queue
if [ -z "${TARGET}" ]; then
    TARGET="$(agentkit spotlight-queue next 2>/dev/null || true)"
    if [ -z "${TARGET}" ]; then
        echo "ERROR: No --target given and spotlight queue is empty or unavailable." >&2
        exit 1
    fi
    USE_QUEUE=1
else
    USE_QUEUE=0
fi

# ── 1. Check frigatebird (skip in dry-run) ─────────────────────────────────
if [ "${DRY_RUN}" -eq 0 ] && ! command -v frigatebird &>/dev/null; then
    echo "ERROR: frigatebird not found in PATH. Install it before using this script." >&2
    mkdir -p "${LOG_DIR}"
    printf '%s\n' "$(jq -nc \
        --arg ts "${DATE_NOW}" \
        --arg date "${DATE_SHORT}" \
        --arg tweet_text "" \
        --arg status "error" \
        --arg frigatebird_output "frigatebird not found" \
        --arg share_url "" \
        '{ts: $ts, date: $date, tweet_text: $tweet_text, status: $status, frigatebird_output: $frigatebird_output, share_url: $share_url}')" \
        >> "${LOG_FILE}"
    exit 1
fi

# ── 2. Run spotlight with --share --tweet-only ─────────────────────────────
echo "Running agentkit spotlight --share --tweet-only --target ${TARGET}..."
TWEET_TEXT="$(agentkit spotlight --share --tweet-only --target "${TARGET}" 2>/dev/null || true)"
TWEET_TEXT="${TWEET_TEXT// /}"  # trim
TWEET_TEXT="$(echo "${TWEET_TEXT}" | tr -d '\r')"

# Extract share URL from tweet text (last token starting with https://)
SHARE_URL="$(echo "${TWEET_TEXT}" | grep -oE 'https://[^ ]+' | tail -1 || true)"

if [ -z "${TWEET_TEXT}" ]; then
    echo "ERROR: agentkit spotlight --share --tweet-only returned empty output." >&2
    mkdir -p "${LOG_DIR}"
    printf '%s\n' "$(jq -nc \
        --arg ts "${DATE_NOW}" \
        --arg date "${DATE_SHORT}" \
        --arg tweet_text "" \
        --arg status "error" \
        --arg frigatebird_output "empty tweet_text" \
        --arg share_url "" \
        '{ts: $ts, date: $date, tweet_text: $tweet_text, status: $status, frigatebird_output: $frigatebird_output, share_url: $share_url}')" \
        >> "${LOG_FILE}"
    exit 1
fi

# ── 3. Validate tweet length ───────────────────────────────────────────────
TWEET_LEN="${#TWEET_TEXT}"
if [ "${TWEET_LEN}" -gt 280 ]; then
    echo "ERROR: tweet_text exceeds 280 chars (${TWEET_LEN})." >&2
    mkdir -p "${LOG_DIR}"
    printf '%s\n' "$(jq -nc \
        --arg ts "${DATE_NOW}" \
        --arg date "${DATE_SHORT}" \
        --arg tweet_text "${TWEET_TEXT}" \
        --arg status "error" \
        --arg frigatebird_output "tweet too long: ${TWEET_LEN} chars" \
        --arg share_url "${SHARE_URL}" \
        '{ts: $ts, date: $date, tweet_text: $tweet_text, status: $status, frigatebird_output: $frigatebird_output, share_url: $share_url}')" \
        >> "${LOG_FILE}"
    exit 1
fi

# ── 4. Dry-run: print and exit ─────────────────────────────────────────────
if [ "${DRY_RUN}" -eq 1 ]; then
    echo "[dry-run] Would post tweet (${TWEET_LEN} chars):"
    echo "${TWEET_TEXT}"
    [ -n "${SHARE_URL}" ] && echo "[dry-run] Share URL: ${SHARE_URL}"
    exit 0
fi

# ── 5. Post via frigatebird ────────────────────────────────────────────────
echo "Posting tweet (${TWEET_LEN} chars)..."
FRIGATEBIRD_OUTPUT="$(frigatebird tweet "${TWEET_TEXT}" 2>&1)" && FB_EXIT=0 || FB_EXIT=$?

STATUS="success"
if [ "${FB_EXIT}" -ne 0 ]; then
    STATUS="error"
    echo "ERROR: frigatebird exited ${FB_EXIT}: ${FRIGATEBIRD_OUTPUT}" >&2
fi

# ── 6. Log result ──────────────────────────────────────────────────────────
mkdir -p "${LOG_DIR}"
printf '%s\n' "$(jq -nc \
    --arg ts "${DATE_NOW}" \
    --arg date "${DATE_SHORT}" \
    --arg tweet_text "${TWEET_TEXT}" \
    --arg status "${STATUS}" \
    --arg frigatebird_output "${FRIGATEBIRD_OUTPUT}" \
    --arg share_url "${SHARE_URL}" \
    '{ts: $ts, date: $date, tweet_text: $tweet_text, status: $status, frigatebird_output: $frigatebird_output, share_url: $share_url}')" \
    >> "${LOG_FILE}"

if [ "${STATUS}" = "error" ]; then
    exit 1
fi

# ── 7. Mark done in spotlight-queue (if we used the queue) ────────────────
if [ "${USE_QUEUE}" -eq 1 ]; then
    agentkit spotlight-queue mark-done "github:${TARGET}" 2>/dev/null || true
fi

echo "Done. Spotlight tweet posted successfully."
exit 0
