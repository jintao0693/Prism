#!/usr/bin/env bash
# Prism 本地开发：准备依赖并提示启动命令（macOS / Linux）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Prism local setup (jintao/Prism)"

cd "$ROOT/apps/api"
if [[ ! -d .venv ]]; then
  echo "Creating API venv..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -q -U pip
pip install -q -e ".[dev]"
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created apps/api/.env from example"
fi
deactivate || true

cd "$ROOT/apps/web"
if [[ ! -d node_modules ]]; then
  echo "Installing web deps..."
  npm install
fi
if [[ ! -f .env.local ]]; then
  cat > .env.local <<'EOF'
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_USE_MOCK=false
EOF
  echo "Created apps/web/.env.local (USE_MOCK=false)"
fi

cd "$ROOT"
echo
echo "Setup done. Start in two terminals:"
echo "  1) cd apps/api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000"
echo "  2) cd apps/web && npm run dev"
echo
echo "Demo login: linqing@prism.demo / prism123"
echo "Optional infra: docker compose -f infra/docker-compose.yml up -d"
