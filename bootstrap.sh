#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Prefer python3, fallback to python (important for Windows)
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="${PYTHON_BIN:-python3}"
else
  PYTHON_BIN="${PYTHON_BIN:-python}"
fi

VENV_DIR="${VENV_DIR:-venv}"

echo "==> Using python: $PYTHON_BIN"

# Create virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creating virtual environment at ./$VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# Activate virtual environment (cross-platform)
echo "==> Activating virtual environment"

if [ -f "$VENV_DIR/Scripts/activate" ]; then
  # Windows (Git Bash)
  # shellcheck disable=SC1090
  source "$VENV_DIR/Scripts/activate"
  ACTIVATE_PATH="$VENV_DIR/Scripts/activate"
elif [ -f "$VENV_DIR/bin/activate" ]; then
  # Linux / macOS
  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"
  ACTIVATE_PATH="$VENV_DIR/bin/activate"
else
  echo "❌ Could not find virtual environment activation script"
  exit 1
fi

echo "==> Installing dependencies"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "==> Preparing database and seed data"
mkdir -p database

python - <<'PY'
from app import (
    app,
    db,
    seed_services_catalog,
    backfill_missing_service_prices,
    seed_legacy_blog_posts,
    purge_old_contact_messages,
)
from routes.admin_api import seed_default_admin

with app.app_context():
    db.create_all()
    seed_default_admin()
    seed_services_catalog()
    backfill_missing_service_prices()
    seed_legacy_blog_posts()
    purge_old_contact_messages()

print("Bootstrap complete.")
print("Default admin (if ADMIN_EMAIL/ADMIN_PASSWORD not set): admin@travaa.local / admin123")
PY

echo "==> Done."
echo "==> Start server with:"
echo "   source $ACTIVATE_PATH && python app.py"