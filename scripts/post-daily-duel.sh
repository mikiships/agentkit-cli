#!/usr/bin/env bash
# post-daily-duel.sh — get tweet text from daily-duel and post via frigatebird
# Logs result to ~/.local/share/agentkit/daily-duel-post-log.jsonl
#
# Usage:
#   ./post-daily-duel.sh           — plain tweet (no share URL)
#   ./post-daily-duel.sh --share   — uploads HTML to here.now, tweet includes URL
set -euo pipefail

LOG_DIR="${HOME}/.local/share/agentkit"
LOG_FILE="${LOG_DIR}/daily-duel-post-log.jsonl"
DATE_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DATE_SHORT="$(date -u +%Y-%m-%d)"

# Parse flags
SHARE=0
for arg in "$@"; do
    case "${arg}" in
        --share) SHARE=1 ;;
    esac
done

# ── 1. Check frigatebird is available ──────────────────────────────────────
if ! command -v frigatebird &>/dev/null; then
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

# ── 2. Get tweet text ──────────────────────────────────────────────────────
SHARE_URL=""
if [ "${SHARE}" -eq 1 ]; then
    # --share: upload HTML + include URL in tweet text
    TWEET_TEXT="$(agentkit daily-duel --share --tweet-only 2>/dev/null || true)"
    # Extract share URL from tweet text (last token starting with https://)
    SHARE_URL="$(echo "${TWEET_TEXT}" | grep -oE 'https://[^ ]+' | tail -1 || true)"
    # If upload failed (no URL appended), fall back to plain tweet
    if [ -z "${SHARE_URL}" ]; then
        echo "WARNING: --share upload failed or returned no URL. Falling back to plain tweet." >&2
        TWEET_TEXT="$(agentkit daily-duel --tweet-only 2>/dev/null || true)"
    fi
else
    TWEET_TEXT="$(agentkit daily-duel --tweet-only 2>/dev/null || true)"
fi

TWEET_TEXT="${TWEET_TEXT#"${TWEET_TEXT%%[![:space:]]*}"}"  # ltrim
TWEET_TEXT="${TWEET_TEXT%"${TWEET_TEXT##*[![:space:]]}"}"  # rtrim
TWEET_TEXT="$(echo "${TWEET_TEXT}" | tr -d '\r')"

if [ -z "${TWEET_TEXT}" ]; then
    echo "ERROR: agentkit daily-duel --tweet-only returned empty output." >&2
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

# ── 4. Post via frigatebird ────────────────────────────────────────────────
echo "Posting tweet (${TWEET_LEN} chars)..."
FRIGATEBIRD_OUTPUT="$(frigatebird tweet "${TWEET_TEXT}" 2>&1)" && FB_EXIT=0 || FB_EXIT=$?

STATUS="success"
if [ "${FB_EXIT}" -ne 0 ]; then
    STATUS="error"
    echo "ERROR: frigatebird exited ${FB_EXIT}: ${FRIGATEBIRD_OUTPUT}" >&2
fi

# ── 5. Log result ──────────────────────────────────────────────────────────
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

echo "Done. Tweet posted successfully."
exit 0
