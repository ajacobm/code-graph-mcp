#!/bin/bash
# Start both backend and frontend for development

set -e

echo "Starting CodeNavigator Visualizer (dev mode)"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Start backend
echo -e "${BLUE}[Backend]${NC} Starting FastAPI server on localhost:8000"
codenav-web --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo -e "${BLUE}[Frontend]${NC} Starting Vite dev server on localhost:5173"
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}✓ Services started:${NC}"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
