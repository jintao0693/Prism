# Prism 本地开发：准备依赖并提示启动命令（Windows）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> Prism local setup (jintao/Prism)" -ForegroundColor Cyan

# API
$api = Join-Path $Root "apps\api"
Set-Location $api
if (-not (Test-Path ".venv")) {
  Write-Host "Creating API venv..."
  python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install -q -U pip
& ".\.venv\Scripts\pip.exe" install -q -e ".[dev]"
if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created apps/api/.env from example"
}

# Web
$web = Join-Path $Root "apps\web"
Set-Location $web
if (-not (Test-Path "node_modules")) {
  Write-Host "Installing web deps..."
  npm install
}
if (-not (Test-Path ".env.local")) {
  @"
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_USE_MOCK=false
"@ | Set-Content -Encoding utf8 ".env.local"
  Write-Host "Created apps/web/.env.local (USE_MOCK=false)"
}

Set-Location $Root
Write-Host ""
Write-Host "Setup done. Start in two terminals:" -ForegroundColor Green
Write-Host "  1) cd apps\api; .\.venv\Scripts\activate; uvicorn app.main:app --reload --port 8000"
Write-Host "  2) cd apps\web; npm run dev"
Write-Host ""
Write-Host "Demo login: linqing@prism.demo / prism123"
Write-Host "Optional infra: docker compose -f infra/docker-compose.yml up -d"
