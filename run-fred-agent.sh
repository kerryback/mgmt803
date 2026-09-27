#!/usr/bin/env bash
# Start the FRED agent for the session 24 demo.
#
#   ./run-fred-agent.sh
#
# Then, on the projector:
#
#   browser  http://localhost:8001/?what is the unemployment rate now
#
#   curl     curl -s -X POST http://localhost:8001/ask \
#              -H "Content-Type: application/json" \
#              -d '{"question": "what is the unemployment rate now?"}'
#
# Keep this terminal visible. Every FRED call and every line of Python the
# agent writes is printed here as it happens.
set -euo pipefail
cd "$(dirname "$0")"

KEYFILE="$HOME/repos/lab-june/.env"
PORT=8001

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    if [ -f "$KEYFILE" ]; then
        ANTHROPIC_API_KEY=$(grep -m1 '^ANTHROPIC_API_KEY_2=' "$KEYFILE" | cut -d= -f2-)
        export ANTHROPIC_API_KEY
    else
        echo "No ANTHROPIC_API_KEY set and $KEYFILE not found." >&2
        echo "Export a key and run this again." >&2
        exit 1
    fi
fi

# Fail now, in front of nobody, rather than on the first question in class.
python3 - <<'CHECK'
import sys, anthropic
try:
    anthropic.Anthropic().messages.create(
        model="claude-opus-5", max_tokens=8,
        messages=[{"role": "user", "content": "ok"}])
except Exception as e:
    sys.exit(f"Key check failed: {type(e).__name__}: {e}")
print("key ok")
CHECK

lsof -ti "tcp:$PORT" >/dev/null 2>&1 && {
    echo "Something is already listening on port $PORT:" >&2
    lsof -i "tcp:$PORT" >&2
    exit 1
}

echo
echo "  browser   http://localhost:$PORT/?what is the unemployment rate now"
echo
echo "  curl      curl -s -X POST http://localhost:$PORT/ask \\"
echo "              -H 'Content-Type: application/json' \\"
echo "              -d '{\"question\": \"what is the unemployment rate now?\"}'"
echo
exec python3 -m uvicorn fred_agent:app --port "$PORT"
