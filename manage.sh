#!/bin/bash

# Industrial RAG Demonstrator - App Manager Script

PID_FILE=".app.pids"
BACKEND_LOG="backend.log"
FRONTEND_LOG="frontend.log"

# Colors for terminal styling
CYAN='\033[0;36m'
PINK='\033[0;35m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Load environment variables from .env if present
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

usage() {
  echo -e "Usage: $0 {${CYAN}start-prod${NC}|${CYAN}start-dev${NC}|${CYAN}stop${NC}|${CYAN}status${NC}|${CYAN}restart${NC}|${CYAN}logs${NC}}"
  echo -e "  ${CYAN}start-prod${NC} : Starts the FastAPI backend (serves pre-built frontend from http://localhost:7860)"
  echo -e "  ${CYAN}start-dev${NC}  : Starts backend (port 7860) & Vite frontend (port 5173 with hot reload)"
  echo -e "  ${CYAN}stop${NC}       : Stops all running app processes"
  echo -e "  ${CYAN}status${NC}     : Checks process states and print links"
  echo -e "  ${CYAN}restart${NC}    : Stops and restarts the last start mode (default: start-prod)"
  echo -e "  ${CYAN}logs${NC}       : Tails the backend and frontend logs"
}

check_api_key() {
  if [ -z "$CEREBRAS_API_KEY" ] || [ "$CEREBRAS_API_KEY" = "paste-your-cerebras-key-here" ]; then
    echo -e "${RED}Warning: CEREBRAS_API_KEY is not configured or uses placeholder value.${NC}"
    echo -e "Please configure CEREBRAS_API_KEY in your .env file."
  fi
}

start_prod() {
  echo -e "${CYAN}Starting Industrial RAG Demonstrator in Production Mode...${NC}"
  check_api_key

  # Check if already running
  if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}App seems to be running already. Use 'stop' or 'restart' first.${NC}"
    return 1
  fi

  # Start backend uvicorn (which serves the pre-built files in static/)
  echo -e "Starting Uvicorn backend server on port 7860..."
  nohup uvicorn backend.main:app --host 127.0.0.1 --port 7860 > "$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  
  echo "$BACKEND_PID" > "$PID_FILE"
  echo "prod" >> "$PID_FILE"

  # Wait a moment for server initialization
  sleep 1.5

  if kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "${GREEN}Backend started successfully!${NC}"
    echo -e "Pre-built Frontend served at: ${CYAN}http://localhost:7860${NC}"
    echo -e "Backend Health checks:        ${CYAN}http://localhost:7860/health${NC}"
  else
    echo -e "${RED}Failed to start backend server. Check logs: cat $BACKEND_LOG${NC}"
    rm -f "$PID_FILE"
  fi
}

start_dev() {
  echo -e "${CYAN}Starting Industrial RAG Demonstrator in Development Mode...${NC}"
  check_api_key

  # Check if already running
  if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}App seems to be running already. Use 'stop' or 'restart' first.${NC}"
    return 1
  fi

  # 1. Start backend
  echo -e "Starting Uvicorn backend server on port 7860..."
  nohup uvicorn backend.main:app --host 127.0.0.1 --port 7860 > "$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!

  # 2. Start Vite
  echo -e "Starting Vite dev server on port 5173..."
  nohup npm run dev --prefix frontend > "$FRONTEND_LOG" 2>&1 &
  FRONTEND_PID=$!

  echo "$BACKEND_PID" > "$PID_FILE"
  echo "$FRONTEND_PID" >> "$PID_FILE"
  echo "dev" >> "$PID_FILE"

  sleep 2.0

  BACKEND_RUNNING=false
  FRONTEND_RUNNING=false
  kill -0 "$BACKEND_PID" 2>/dev/null && BACKEND_RUNNING=true
  kill -0 "$FRONTEND_PID" 2>/dev/null && FRONTEND_RUNNING=true

  if [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
    echo -e "${GREEN}Development environment launched successfully!${NC}"
    echo -e "Frontend (Vite hot-reload):   ${CYAN}http://localhost:5173${NC}"
    echo -e "Backend Endpoint API:         ${CYAN}http://localhost:7860${NC}"
    echo -e "Backend Health checks:        ${CYAN}http://localhost:7860/health${NC}"
  else
    [ "$BACKEND_RUNNING" = false ] && echo -e "${RED}Failed to start backend. Check logs: cat $BACKEND_LOG${NC}"
    [ "$FRONTEND_RUNNING" = false ] && echo -e "${RED}Failed to start frontend. Check logs: cat $FRONTEND_LOG${NC}"
    stop
  fi
}

stop() {
  echo -e "${PINK}Stopping all Industrial RAG processes...${NC}"
  if [ -f "$PID_FILE" ]; then
    # Read pids
    mapfile -t PIDS < "$PID_FILE"
    # The last element is the mode indicator
    unset 'PIDS[${#PIDS[@]}-1]'
    
    for PID in "${PIDS[@]}"; do
      if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Killing process $PID..."
        kill "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null
      fi
    done
    rm -f "$PID_FILE"
  else
    # Fallback to process names
    echo "No PID file found. Searching for running processes..."
    
    UVICORN_PIDS=$(pgrep -f "uvicorn backend.main:app")
    if [ -n "$UVICORN_PIDS" ]; then
      echo "Stopping backend (PIDs: $UVICORN_PIDS)..."
      kill -9 $UVICORN_PIDS 2>/dev/null
    fi

    VITE_PIDS=$(pgrep -f "vite")
    if [ -n "$VITE_PIDS" ]; then
      echo "Stopping Vite server (PIDs: $VITE_PIDS)..."
      kill -9 $VITE_PIDS 2>/dev/null
    fi
  fi
  echo -e "${GREEN}Stopped.${NC}"
}

status() {
  echo -e "${CYAN}Checking application status...${NC}"
  
  # Check backend on 7860
  BACKEND_PID=$(pgrep -f "uvicorn backend.main:app")
  if [ -n "$BACKEND_PID" ]; then
    echo -e "Backend Server (uvicorn): ${GREEN}RUNNING${NC} (PIDs: $BACKEND_PID)"
    echo -e "  - Link: ${CYAN}http://localhost:7860/health${NC}"
  else
    echo -e "Backend Server (uvicorn): ${RED}STOPPED${NC}"
  fi

  # Check frontend on 5173
  FRONTEND_PID=$(pgrep -f "vite")
  if [ -n "$FRONTEND_PID" ]; then
    echo -e "Frontend Dev Server (Vite): ${GREEN}RUNNING${NC} (PIDs: $FRONTEND_PID)"
    echo -e "  - Link: ${CYAN}http://localhost:5173${NC}"
  else
    # Check if prod mode index is served on 7860
    if [ -n "$BACKEND_PID" ]; then
      echo -e "Frontend Server (Production Mode): ${GREEN}RUNNING${NC} (via backend port 7860)"
      echo -e "  - Link: ${CYAN}http://localhost:7860${NC}"
    else
      echo -e "Frontend Server (dev/prod): ${RED}STOPPED${NC}"
    fi
  fi
}

restart() {
  MODE="prod"
  if [ -f "$PID_FILE" ]; then
    # Read the last line for the mode indicator
    MODE=$(tail -n 1 "$PID_FILE")
    stop
  else
    stop
  fi

  sleep 1.0
  if [ "$MODE" = "dev" ]; then
    start_dev
  else
    start_prod
  fi
}

show_logs() {
  echo -e "${CYAN}Tailing application logs... (Ctrl+C to exit)${NC}"
  if [ -f "$FRONTEND_LOG" ]; then
    tail -n 20 -f "$BACKEND_LOG" "$FRONTEND_LOG"
  else
    tail -n 20 -f "$BACKEND_LOG"
  fi
}

case "$1" in
  start-prod)
    start_prod
    ;;
  start-dev)
    start_dev
    ;;
  stop)
    stop
    ;;
  status)
    status
    ;;
  restart)
    restart
    ;;
  logs)
    show_logs
    ;;
  *)
    usage
    exit 1
    ;;
esac
