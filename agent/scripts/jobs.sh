#!/bin/sh
# Create or update the scheduled jobs. Idempotent: existing jobs are edited by name,
# missing ones are created. Runs inside the container as the hermes user:  make jobs
set -eu

PROMPTS=/opt/hja/prompts
ENV_FILE=${HERMES_HOME:-/opt/data}/.env

# Attach the alert-mailbox collector only when a mailbox is configured.
if grep -q '^SCOUT_IMAP_HOST=..*' "$ENV_FILE" 2>/dev/null; then
  ALERT_SCRIPT=fetch_alerts.py
else
  ALERT_SCRIPT=""
fi

# upsert NAME SCHEDULE PROMPT_FILE SCRIPT [flags shared by create and edit...]
upsert() {
  name=$1 schedule=$2 prompt_file=$3 script=$4
  shift 4
  prompt=$(cat "$prompt_file")

  if out=$(hermes cron edit "$name" --schedule "$schedule" --prompt "$prompt" \
             --script "$script" "$@" 2>&1); then
    echo "updated  $name ($schedule)"
  elif printf '%s' "$out" | grep -q "Job not found"; then
    if [ -n "$script" ]; then
      hermes cron create "$schedule" "$prompt" --name "$name" --script "$script" "$@" >/dev/null
    else
      hermes cron create "$schedule" "$prompt" --name "$name" "$@" >/dev/null
    fi
    echo "created  $name ($schedule)"
  else
    printf 'failed   %s\n%s\n' "$name" "$out" >&2
    return 1
  fi
}

upsert scout "every 12h" "$PROMPTS/scout.md" "$ALERT_SCRIPT" \
  --skill scout-profile --skill scout-tracker --deliver telegram --catch-up on

upsert deadlines "every 24h" "$PROMPTS/deadlines.md" "" \
  --skill scout-tracker --deliver telegram --catch-up on

# Weekly market brief: Mondays 08:00 in HJA_TIMEZONE (set in .env; default UTC).
upsert brief "0 8 * * 1" "$PROMPTS/market-brief.md" "" \
  --skill career-advisor --skill scout-profile --skill scout-tracker \
  --timezone "${HJA_TIMEZONE:-UTC}" --deliver telegram --catch-up on

# Daily research radar: 07:00. The script collects arXiv papers and OpenAlex citations.
upsert radar "0 7 * * *" "$PROMPTS/radar.md" research_radar.py \
  --skill research-radar --skill scout-profile \
  --timezone "${HJA_TIMEZONE:-UTC}" --deliver telegram --catch-up on

# Weekly calls radar (short stays, schools, workshop calls, travel grants): Wednesdays 08:00.
upsert calls "0 8 * * 3" "$PROMPTS/calls.md" "" \
  --skill calls-radar --skill scout-profile --skill scout-tracker \
  --timezone "${HJA_TIMEZONE:-UTC}" --deliver telegram --catch-up on

# Monthly mobility check (visa and residency routes): 15th of each month, 09:00.
upsert mobility "0 9 15 * *" "$PROMPTS/mobility.md" "" \
  --skill mobility-intel --skill scout-profile \
  --timezone "${HJA_TIMEZONE:-UTC}" --deliver telegram --catch-up on

# Monthly three-month plan: 1st of each month, 09:00 in HJA_TIMEZONE.
upsert strategy "0 9 1 * *" "$PROMPTS/strategy.md" "" \
  --skill strategist --skill scout-profile --skill scout-tracker --skill career-advisor \
  --timezone "${HJA_TIMEZONE:-UTC}" --deliver telegram --catch-up on

echo
hermes cron list
