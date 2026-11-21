#!/bin/sh
# Creates the two scheduled jobs. Run INSIDE the container:
#   docker exec -it -u 10000 hermes sh
#   sh /opt/data/scout-scripts/create-jobs.sh
# Requires the scout-profile and scout-tracker skills to exist (see README).
# To recreate after editing prompts: hermes cron list, hermes cron remove <id>, run this again.
set -eu

P=/opt/data/prompts

# Use the alert-mailbox collector only if a mailbox is configured
SCRIPT_ARG=""
if grep -q '^SCOUT_IMAP_HOST=' /opt/data/.env 2>/dev/null; then
  SCRIPT_ARG="--script /opt/data/scout-scripts/fetch_alerts.py"
fi

hermes cron create "every 12h" "$(cat $P/scout.md)" \
  $SCRIPT_ARG \
  --skill scout-profile --skill scout-tracker \
  --deliver telegram --name scout

hermes cron create "every 24h" "$(cat $P/deadlines.md)" \
  --skill scout-tracker \
  --deliver telegram --name deadlines

hermes cron list
