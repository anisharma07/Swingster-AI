#!/usr/bin/env bash
# ==============================================================================
#  Swingster AI: Indian Equities Swing Trading Dashboard & Research Server
#  Starts the interactive web application on http://localhost:5001
# ==============================================================================

PORT=${PORT:-5001}
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================================${NC}"
echo -e "${BOLD}${GREEN}  🚀 Starting Swingster AI Dashboard on http://localhost:${PORT}${NC}"
echo -e "${CYAN}================================================================${NC}"

# Check if port is already occupied and free it
OCCUPIED_PID=$(lsof -ti:${PORT} 2>/dev/null)
if [ -n "$OCCUPIED_PID" ]; then
  echo -e "${YELLOW}⚠️  Port ${PORT} is currently in use by PID ${OCCUPIED_PID}.${NC}"
  echo -e "${YELLOW}   Stopping previous process...${NC}"
  kill -9 ${OCCUPIED_PID} 2>/dev/null
  sleep 0.5
fi

# Locate Python environment
if [ -f "$DIR/.venv/bin/python3" ]; then
  PYTHON_EXEC="$DIR/.venv/bin/python3"
elif [ -f "$DIR/.venv/bin/python" ]; then
  PYTHON_EXEC="$DIR/.venv/bin/python"
else
  PYTHON_EXEC="python3"
fi

cd "$DIR"
export PORT=${PORT}

echo -e "${GREEN}✓ Using Python:${NC} ${PYTHON_EXEC}"
echo -e "${GREEN}✓ Open Dashboard:${NC} ${BOLD}${CYAN}http://localhost:${PORT}${NC}"
echo -e "${GREEN}✓ API Endpoints:${NC} ${CYAN}http://localhost:${PORT}/api/market-regime${NC}, ${CYAN}/api/stock/<symbol>${NC}"
echo -e "${CYAN}----------------------------------------------------------------${NC}"

# Execute app.py
exec "$PYTHON_EXEC" app.py "$@"
