#!/usr/bin/env bash
set -euo pipefail

# Safe Sprint 3 release helper for Foodify FastAPI Cloud + Aiven MySQL.
# Run ONLY after logging in cleanly via: fastapi login

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${BACK_DIR}"

if ! command -v fastapi >/dev/null 2>&1; then
  echo "fastapi CLI not found in PATH. Activate back/.venv first." >&2
  exit 1
fi

echo "[1/3] Checking Alembic migration head & database readiness..."
APP_ENV=production .venv/bin/python -m alembic heads
APP_ENV=production .venv/bin/python -m alembic current || true

echo "[2/3] Applying Sprint 3 schema migration (20261121_0006) & seeding roles..."
APP_ENV=production .venv/bin/python -m scripts.release

echo "[3/3] Deploying FastAPI Cloud service (app.hosted:app)..."
fastapi deploy

echo "Done. Optional: verify SMTP/Brevo/Resend deliverability with:"
echo "  cd back && .venv/bin/python -m scripts.check_email --to <your-test-inbox>"
