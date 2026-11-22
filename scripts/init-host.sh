#!/usr/bin/env bash
# One-time host setup (make init). Safe to re-run: never overwrites existing files.
#  - creates the data folders outside the repo
#  - copies the templates into them
#  - creates .env (dashboard password, your UID/GID) and secrets.env (to fill in)
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
HERMES_DATA="${HERMES_DATA:-$HOME/.hermes}"
SCOUT_MATERIALS="${SCOUT_MATERIALS:-$HOME/scout/materials}"
SCOUT_OUT="${SCOUT_OUT:-$HOME/scout/out}"
UID_NOW="$(id -u)"
GID_NOW="$(id -g)"
if [ "$UID_NOW" -eq 0 ]; then
  echo "Run make init as your normal user, not root: Hermes refuses to run its gateway as root." >&2
  exit 1
fi

say() { printf '  %-10s %s\n' "$1" "$2"; }

echo "Folders"
mkdir -p "$HERMES_DATA" "$SCOUT_MATERIALS" "$SCOUT_OUT/drafts" "$SCOUT_OUT/briefs"
say "state" "$HERMES_DATA"
say "materials" "$SCOUT_MATERIALS"
say "output" "$SCOUT_OUT"

echo "Templates (existing files are kept)"
copy_new() {  # copy_new SRC_DIR DEST_DIR: copy files that don't exist yet
  for src in "$1"/*; do
    dest="$2/$(basename "$src")"
    [ -e "$dest" ] || cp -R "$src" "$dest"
  done
}
copy_new "$REPO/templates/materials" "$SCOUT_MATERIALS"
copy_new "$REPO/templates/out" "$SCOUT_OUT"
find "$SCOUT_MATERIALS" -type d -exec chmod 755 {} +
find "$SCOUT_MATERIALS" -type f -exec chmod 644 {} +
say "copied" "criteria.md, sources.md, guides/, applications.md, seen.md"

echo "Config files"
if [ ! -f "$REPO/.env" ]; then
  sed -e "s/^DASH_PASS=.*/DASH_PASS=$(openssl rand -hex 16)/" \
      -e "s/^HERMES_UID=.*/HERMES_UID=$UID_NOW/" \
      -e "s/^HERMES_GID=.*/HERMES_GID=$GID_NOW/" \
      "$REPO/.env.example" > "$REPO/.env"
  chmod 600 "$REPO/.env"
  say "created" ".env (dashboard: admin / DASH_PASS)"
else
  say "kept" ".env"
fi
if [ ! -f "$REPO/secrets.env" ]; then
  cp "$REPO/secrets.env.example" "$REPO/secrets.env"
  chmod 600 "$REPO/secrets.env"
  say "created" "secrets.env (fill in, then: make configure)"
else
  say "kept" "secrets.env"
fi

# Existing installs created for the default container user (10000) need one re-own,
# because Hermes now runs as you. The container re-owns its own subfolders, not top-level files.
for dir in "$HERMES_DATA" "$SCOUT_OUT"; do
  if [ -n "$(find "$dir" -maxdepth 2 ! -uid "$UID_NOW" -print -quit 2>/dev/null)" ]; then
    echo
    echo "Note: $dir contains files owned by another user. Take them over once with:"
    echo "  sudo chown -R $UID_NOW:$GID_NOW $dir"
  fi
done

echo
echo "Next: put your CV in $SCOUT_MATERIALS, edit criteria.md and sources.md, fill in secrets.env."
