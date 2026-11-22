# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `PermissionError: [Errno 13]` on `/opt/data/...` | Files in `~/.hermes` owned by a different user, often from a non-Docker Hermes install using the same folder, or an older install running as UID 10000. | `make down`, `sudo chown -R $(id -u):$(id -g) ~/.hermes ~/scout/out`, check `HERMES_UID`/`HERMES_GID` in `.env`, `make up`. Don't run a native `hermes` against `~/.hermes`. |
| `HTTP 401: invalid x-api-key` | Hermes' built-in Anthropic provider has a missing or wrong key. | `make login` for the subscription route, or set a valid key with `hermes model`. |
| `DDGS search error: No results found` | DuckDuckGo throttles scraped searches. | Set `BRAVE_SEARCH_API_KEY` in `secrets.env`, then `make configure && make restart`. |
| `search-only backend` when reading a page | No page-reading provider. | Set `TAVILY_API_KEY`, then `make configure && make restart`. |
| `execute_code … BLOCKED` in cron runs | Code execution still enabled. | `make configure && make restart`. |
| A run ends with `KeyboardInterrupt` | The container restarted during the run. | `make run` again; avoid restarts while a run is in progress. |
| Bot posts its intermediate steps | Display settings not applied. | `make configure && make restart`. |
| Bot doesn't answer | Missing or wrong Telegram values. | Check `TELEGRAM_*` in `secrets.env` (`TELEGRAM_ALLOWED_USERS` is your numeric ID), `make configure && make restart`, then `make logs` and look for Telegram lines. |
| No scheduled reports arrive | Jobs missing, or no home channel. | `make status`; set `TELEGRAM_HOME_CHANNEL`; `make configure && make jobs`. |
| `Script path must be relative to …/scripts/` | A cron script outside Hermes' scripts folder. | `make install && make jobs`. |
| Browser tools fail on some pages | Not enough shared memory for Chromium. | `shm_size: 1g` is set in `compose.yml`; recreate with `make down && make up`. |
| The bot says your materials are missing or "templates unfilled" | Your files are in the repo's `templates/` (never read), or the `materials`/`out` folder was deleted and recreated while Hermes ran. | Put your files in `~/scout/materials/`, then `make down && make up` and `make profile`. Restore the templates with `git checkout -- templates && git clean -fd templates`. |
| Edits to `templates/` have no effect | `make init` copies templates once and never overwrites. | Edit `~/scout/materials/` instead. |
| Radar digest notes "arXiv query skipped (429)" | arXiv rate-limited the server's IP for a while. | Nothing: the radar stops for the day and tries again tomorrow. If it persists, reduce the number of queries in `radar.json`. |
| Radar says "Citation tracking off" | `OPENALEX_API_KEY` or `openalex_author_id` missing. | Add the key to `secrets.env` (`make configure && make restart`) and your author ID to `radar.json`. |
| Radar says `NO_RADAR_CONFIG` | No `~/scout/materials/radar.json`. | `bash scripts/init-host.sh` copies the template; then edit it. |
| Profile skill has the wrong rubric | The agent paraphrased instead of copying. | Tell the bot what is wrong and ask it to update scout-profile, or edit `~/.hermes/skills/hja/scout-profile/SKILL.md`. |
