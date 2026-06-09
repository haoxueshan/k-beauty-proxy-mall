#!/usr/bin/env bash
set -euo pipefail

PUBLIC_DOMAIN="${1:-}"

echo "[local] backend health"
curl -fsS http://127.0.0.1:8000/health
echo

echo "[local] backend readiness"
curl -fsS http://127.0.0.1:8000/health/ready
echo

echo "[local] frontend root"
curl -fsS http://127.0.0.1:3000 > /dev/null
echo "ok"

if [[ -n "$PUBLIC_DOMAIN" ]]; then
  echo "[public] health"
  curl -fsS "https://${PUBLIC_DOMAIN}/health"
  echo

  echo "[public] search"
  curl -fsS "https://${PUBLIC_DOMAIN}/api/oliveyoung/search?q=%E7%89%99%E8%86%8F" > /dev/null
  echo "ok"
fi
