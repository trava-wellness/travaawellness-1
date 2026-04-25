#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-venv}"

echo "==> Using python: $PYTHON_BIN"

if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creating virtual environment at ./$VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

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

echo "==> Done. Start server with: source $VENV_DIR/bin/activate && python app.py"
