#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="/www/wwwroot/k-beauty-proxy-mall"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "[1/4] Installing frontend dependencies"
cd "$FRONTEND_DIR"
npm install
npm run build

echo "[2/4] Creating backend virtual environment"
cd "$BACKEND_DIR"
python3 -m venv .venv
source .venv/bin/activate

echo "[3/4] Installing backend dependencies"
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/4] Installing Playwright browser dependencies"
python -m playwright install --with-deps chromium || python -m playwright install chromium || true

echo "Bootstrap completed."
echo "Next steps:"
echo "1. Fill frontend/.env.local and backend/.env"
echo "2. Start frontend with PM2 using deploy/baota/frontend.ecosystem.config.js"
echo "3. Start backend with Supervisor using deploy/baota/backend.supervisor.conf"
echo "4. Apply Nginx configs from deploy/baota/"
