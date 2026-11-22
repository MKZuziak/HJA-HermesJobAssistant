#!/bin/sh
# Install this repo's agent assets into Hermes' data folder.
# Runs inside the container as the hermes user:  make install
# Safe to re-run: repo-owned files are replaced, everything else is left alone.
set -eu

SRC=/opt/hja
DATA=${HERMES_HOME:-/opt/data}

# Skills shipped with the repo go into their own category folder: skills/hja/<name>/.
# The generated scout-profile skill also lives there but is never touched here.
mkdir -p "$DATA/skills/hja"
for dir in "$SRC"/skills/*/; do
  name=$(basename "$dir")
  rm -rf "${DATA:?}/skills/hja/$name"
  cp -R "$dir" "$DATA/skills/hja/$name"
  echo "skill      hja/$name"
done

# Cron scripts must live in Hermes' own scripts folder (absolute paths are refused).
mkdir -p "$DATA/scripts"
for script in fetch_alerts.py research_radar.py; do
  cp "$SRC/scripts/$script" "$DATA/scripts/$script"
  echo "script     scripts/$script"
done

# Standing rules loaded into every session.
cp "$SRC/SOUL.md" "$DATA/SOUL.md"
echo "rules      SOUL.md"
