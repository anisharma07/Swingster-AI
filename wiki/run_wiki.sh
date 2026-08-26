#!/usr/bin/env bash
# ==============================================================================
#  LM Wiki Reader Launcher Script
#  Starts the local documentation server on http://localhost:5111
# ==============================================================================

PORT=5111
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "--------------------------------------------------------"
echo "  🚀 Starting LM Wiki Reader on http://localhost:${PORT}"
echo "--------------------------------------------------------"

# Check if port 5111 is already occupied and ask/free it
OCCUPIED_PID=$(lsof -ti:${PORT} 2>/dev/null)
if [ -n "$OCCUPIED_PID" ]; then
  echo "⚠️  Port ${PORT} is currently in use by PID ${OCCUPIED_PID}."
  echo "   Killing previous process..."
  kill -9 ${OCCUPIED_PID} 2>/dev/null
  sleep 0.5
fi

# Run Python 3 server
cd "$DIR"
python3 wiki_server.py --port ${PORT} "$@"
