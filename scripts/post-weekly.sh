#!/usr/bin/env bash
# post-weekly.sh — generate weekly agentkit digest and optionally save/share it
# Logs result to ~/.local/share/agentkit/weekly-post-log.jsonl
#
# Usage:
#   ./post-weekly.sh               — print tweet text to stdout + log
#   ./post-weekly.sh --share       — also upload HTML report to here.now
#   ./post-weekly.sh --tweet-only  — print tweet text only, no log, no HTML
#   ./post-weekly.sh --days 14     — look back 14 days instead of 7
#   ./post-weekly.sh --output /path/to/report.html  — save HTML to file
#
# NOTE: This script does NOT call frigatebird or any external tweet API.
#       To post, pipe the output to your preferred posting tool.
set -euo pipefail

LOG_DIR="${HOME}/.local/share/agentkit"
LOG_FILE="${LOG_DIR}/weekly-post-log.jsonl"
DATE_NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DATE_SHORT="$(date -u +%Y-%m-%d)"

# ── Parse flags ─────────────────────────────────────────────────────────────
SHARE=0
TWEET_ONLY=0
DAYS=7
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --share)       SHARE=1;        shift ;;
        --tweet-only)  TWEET_ONLY=1;   shift ;;
        --days)        DAYS="$2";      shift 2 ;;
        --output)      OUTPUT="$2";    shift 2 ;;
        --days=*)      DAYS="${1#*=}"; shift ;;
        --output=*)    OUTPUT="${1#*=}"; shift ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# ── 1. Verify agentkit is available ─────────────────────────────────────────
if ! command -v agentkit &>/dev/null; then
    echo "ERROR: agentkit not found in PATH." >&2
    exit 1
fi

# ── 2. Get tweet text ───────────────────────────────────────────────────────
TWEET_TEXT="$(agentkit weekly --tweet-only --days "${DAYS}" 2>/dev/null || true)"

TWEET_TEXT="${TWEET_TEXT#"${TWEET_TEXT%%[![:space:]]*}"}"  # ltrim
TWEET_TEXT="${TWEET_TEXT%"${TWEET_TEXT##*[![:space:]]}"}"  # rtrim
TWEET_TEXT="$(echo "${TWEET_TEXT}" | tr -d '\r')"

if [ -z "${TWEET_TEXT}" ]; then
    echo "ERROR: agentkit weekly --tweet-only returned empty output." >&2
    exit 1
fi

# ── 3. --tweet-only: print and exit ─────────────────────────────────────────
if [ "${TWEET_ONLY}" -eq 1 ]; then
    echo "${TWEET_TEXT}"
    exit 0
fi

# ── 4. Validate tweet length ─────────────────────────────────────────────────
TWEET_LEN="${#TWEET_TEXT}"
if [ "${TWEET_LEN}" -gt 280 ]; then
    echo "ERROR: tweet_text exceeds 280 chars (${TWEET_LEN})." >&2
    exit 1
fi

# ── 5. Optional: save HTML to --output ───────────────────────────────────────
HTML_PATH=""
if [ -n "${OUTPUT}" ]; then
    agentkit weekly --output "${OUTPUT}" --days "${DAYS}" --quiet 2>/dev/null || true
    HTML_PATH="${OUTPUT}"
    echo "HTML report saved to ${OUTPUT}"
fi

# ── 6. Optional: upload HTML via --share ─────────────────────────────────────
SHARE_URL=""
if [ "${SHARE}" -eq 1 ]; then
    # Capture share URL from agentkit weekly --share --quiet
    SHARE_URL="$(agentkit weekly --share --quiet --days "${DAYS}" 2>/dev/null | grep -oE 'https://[^ ]+' | head -1 || true)"
    if [ -n "${SHARE_URL}" ]; then
        echo "Weekly report published: ${SHARE_URL}"
    else
        echo "WARNING: --share upload returned no URL." >&2
    fi
fi

# ── 7. Print tweet to stdout ─────────────────────────────────────────────────
echo ""
echo "Tweet (${TWEET_LEN} chars):"
echo "---"
echo "${TWEET_TEXT}"
echo "---"

# ── 8. Log result ────────────────────────────────────────────────────────────
mkdir -p "${LOG_DIR}"
printf '%s\n' "$(printf '{"ts":"%s","date":"%s","tweet_text":"%s","share_url":"%s","days":%s,"html_path":"%s","status":"success"}' \
    "${DATE_NOW}" \
    "${DATE_SHORT}" \
    "$(echo "${TWEET_TEXT}" | sed 's/"/\\"/g' | tr '\n' ' ')" \
    "${SHARE_URL}" \
    "${DAYS}" \
    "${HTML_PATH}")" \
    >> "${LOG_FILE}"

echo "Done. Log: ${LOG_FILE}"
exit 0
