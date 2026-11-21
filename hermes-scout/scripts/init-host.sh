#!/usr/bin/env bash
# One-time host setup: creates the data folders outside the repo, copies the
# templates, sets permissions for the container user (uid 10000) and creates
# .env with a random dashboard password. Safe to re-run: never overwrites files.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_DATA="${HERMES_DATA:-$HOME/.hermes}"
SCOUT_MATERIALS="${SCOUT_MATERIALS:-$HOME/scout/materials}"
SCOUT_OUT="${SCOUT_OUT:-$HOME/scout/out}"
ME="$(id -u)"

echo "Data folders:"
echo "  Hermes state : $HERMES_DATA"
echo "  Materials    : $SCOUT_MATERIALS"
echo "  Output       : $SCOUT_OUT"

mkdir -p "$HERMES_DATA" "$SCOUT_MATERIALS" "$SCOUT_OUT/drafts"

# Templates (no overwrite)
cp -n "$REPO"/templates/materials/* "$SCOUT_MATERIALS"/
cp -n "$REPO"/templates/out/* "$SCOUT_OUT"/

# Materials: yours, readable by the container
find "$SCOUT_MATERIALS" -type d -exec chmod 755 {} +
find "$SCOUT_MATERIALS" -type f -exec chmod 644 {} +

# Hermes state and output: owned by the container user, with access for you
sudo chown -R 10000:10000 "$HERMES_DATA" "$SCOUT_OUT"
sudo setfacl -R -m "u:$ME:rwX" -m "d:u:$ME:rwX" -m m::rwX -m d:m::rwX "$SCOUT_OUT"

# Compose .env with a random dashboard password
if [ ! -f "$REPO/.env" ]; then
  echo "DASH_PASS=$(openssl rand -hex 16)" > "$REPO/.env"
  chmod 600 "$REPO/.env"
  echo "Created $REPO/.env (dashboard login: admin / value of DASH_PASS)"
fi

echo "Done. Next: edit $SCOUT_MATERIALS/criteria.md and sources.md, then run the setup wizard (see README)."
