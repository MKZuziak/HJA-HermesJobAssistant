# Setup

About 30 minutes. Every step is a `make` target; run `make` to list them.

## Prerequisites

- Linux with Docker Engine and the Compose plugin (developed on Fedora with SELinux enforcing).
- A model: a Claude Pro/Max subscription, or any provider in [models.md](models.md).
- Free accounts: a Telegram bot ([@BotFather](https://t.me/BotFather)), [Brave Search API](https://api-dashboard.search.brave.com), [Tavily](https://app.tavily.com).
- Optional: a dedicated mailbox with IMAP access for job alerts.

## 1. Clone and initialise

```sh
git clone https://github.com/MKZuziak/HJA-HermesJobAssistant.git ~/hja && cd ~/hja
make init
```

`make init` creates `~/.hermes`, `~/scout/materials` and `~/scout/out`, copies the templates, and writes two gitignored files: `.env` (random dashboard password, your UID/GID, image tag) and `secrets.env` (to fill in).

## 2. Your materials

The agent reads **only `~/scout/materials/`**. The repo's `templates/` folder is just the starting point `make init` copies from, once; editing it afterwards changes nothing, and anything you put there can be committed and published. Keep your real files in `~/scout/materials/`:

- Your CV: `.tex` and/or `.pdf`. Subfolders are fine.
- Past applications or cover letters (optional, recommended): the profile learns your writing style from them.
- `criteria.md`: who you are, topics, roles, location priority, hard exclusions, scoring rubric and thresholds.
- `sources.md`: the sites and search queries to check each run.
- `guides/` (optional): CV and application guides the career advisor should follow.
- `calls.md`: programme pages, venues and queries for the calls radar (visits, short fellowships, schools, travel grants).
- `radar.json`: arXiv queries and categories for the research radar, and your OpenAlex author ID for citation tracking (find it by searching your name on openalex.org; it starts with `A`).
- The *Mobility facts* section of `criteria.md`: facts visa rules use (citizenship, degrees, experience, languages). Leave out anything you prefer; the mobility check lists what's missing.

Copying from another machine: `rsync -a ~/scout/materials/ <server>:~/scout/materials/`.

You can add and edit files here at any time, even while Hermes runs. Don't delete and recreate the `materials` or `out` folders themselves while it runs: the container stays attached to the old folder and sees it as empty until `make down && make up`.

## 3. Secrets and timezone

Fill in `secrets.env`. `TELEGRAM_HOME_CHANNEL` is where reports go; for a private chat with your bot it equals your user ID. `OPENALEX_API_KEY` (free, from openalex.org) turns on citation tracking in the research radar.

In `.env`, set `HJA_TIMEZONE` (e.g. `Europe/Rome`): the radar, briefs, plans and mobility checks run at fixed local times in that zone (see the schedule in [architecture.md](architecture.md#schedule)).

## 4. Build, first-run wizard, start

```sh
make build
make wizard
make up
```

Wizard answers: **Full setup**; model provider **skip** (step 5); terminal backend **local**; browser **local**; messaging **skip**. Tools and web backends are set in step 6, whatever you choose here.

## 5. Model

With a Claude subscription:

```sh
make login
```

This logs Claude Code in (open the printed link, approve, paste the code), installs the subscription plugin, and opens `hermes model`: choose **Claude Subscription DirectSDK (Experimental)**, then **sonnet**. Turn off "extra usage" in your Claude account if you never want to pay beyond the plan.

For any other provider, see [models.md](models.md).

## 6. Configure, install, build the profile, schedule

```sh
make bootstrap
```

which runs, in order:

| Target | Does |
|---|---|
| `make configure` | Writes `secrets.env` into Hermes' `.env` (update-in-place), sets search/extract backends, quiet Telegram output, cron behaviour, and disables terminal and code execution |
| `make restart` | Loads the new settings |
| `make install` | Installs the shipped skills, the `fetch_alerts.py` and `research_radar.py` scripts, and `SOUL.md` |
| `make profile` | Has the agent build the `scout-profile` skill from your materials |
| `make jobs` | Creates (or updates) all scheduled jobs: `scout`, `deadlines`, `radar`, `calls`, `brief`, `strategy`, `mobility` |

All of them are safe to re-run.

## 7. Check

1. Message your bot `hi`: it should answer.
2. Read the generated profile and confirm the rubric, thresholds and exclusions match `criteria.md`:
   ```sh
   cat ~/.hermes/skills/hja/scout-profile/SKILL.md
   ```
3. Run the scout once and wait for the Telegram report (10–20 min):
   ```sh
   make run
   ```
4. Open a few reported links and check the deadlines against the real pages.

## Optional: alert mailbox

1. Create a dedicated mailbox with IMAP (e.g. Posteo, or Gmail with an app password). Subscribe it to saved-search alerts from EURAXESS, jobs.ac.uk, Academic Positions, Nature Careers and similar.
2. Add `SCOUT_IMAP_HOST`, `SCOUT_IMAP_USER`, `SCOUT_IMAP_PASSWORD` to `secrets.env`.
3. `make configure && make jobs`: the scout job picks up the collector automatically.
4. Test the collector on its own:
   ```sh
   docker exec -u hermes hermes python3 /opt/data/scripts/fetch_alerts.py
   ```
