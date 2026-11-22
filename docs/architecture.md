# Architecture

```mermaid
flowchart LR
    subgraph Host["Host (laptop or server)"]
        MAT["~/scout/materials<br/>CV, criteria, sources<br/>read-only"]
        OUT["~/scout/out<br/>drafts, tracker, seen list"]
        HD["~/.hermes<br/>config, secrets, skills,<br/>memory, Claude login"]
        AGT["repo: agent/<br/>prompts, skills, SOUL.md,<br/>scripts — read-only"]
    end

    subgraph C["Container: hermes (runs as your UID)"]
        GW["Gateway<br/>Telegram + cron + dashboard"]
        AG["Agent"]
        CC["Claude Code CLI"]
        BR["Headless Chromium"]
        FA["fetch_alerts.py"]
    end

    AGT -- "make install / make jobs" --> HD
    HD <--> GW
    GW --> AG
    MAT --> AG
    AG --> OUT
    AG --> CC --> CL["Claude<br/>(subscription)"]
    AG -- search --> BRAVE["Brave Search API"]
    AG -- read pages --> TAV["Tavily API"]
    AG --> BR
    MAIL[("Alert mailbox<br/>IMAP")] --> FA --> AG
    GW <--> TG["Telegram"]
```

## Components

| Component | Role |
|---|---|
| **Gateway** | Hermes' long-running service, supervised by s6 inside the container: Telegram connection, cron scheduler, web dashboard. |
| **Agent** | Does the work. Each turn it follows `SOUL.md` (standing rules), the attached skills and the prompt. |
| **Skills** | `scout-tracker`, `career-advisor` and `strategist` ship in `agent/skills/` and are installed as-is. `scout-profile` is generated from your own materials by `make profile`, because it is different for every user. |
| **Cron jobs** | `scout` (every 12 h), `deadlines` (every 24 h) and `brief` (Mondays 08:00) and `strategy` (1st of the month, 09:00), both in `HJA_TIMEZONE`, created and updated by name by `agent/scripts/jobs.sh`. Each run starts fresh; it knows only its prompt and its skills. Missed runs are caught up once when the container returns (`--catch-up on`). |
| **Claude Code CLI** | Baked into the image. With the *Claude Subscription DirectSDK* plugin, model calls go through it, so runs use your Claude subscription rather than a separate API key. Any other provider works too: see [models.md](models.md). |
| **Brave / Tavily** | Web search and page reading (`web.search_backend`, `web.extract_backend`). |
| **Chromium** | Bundled with Hermes, for JavaScript-heavy pages such as Workday job portals. |
| **`fetch_alerts.py`** | Optional. Before each scout run it prints unread job-alert emails from a dedicated mailbox; Hermes injects that output into the run's prompt. |

## Data layout

| Host path | Container path | Contents | In git |
|---|---|---|---|
| repo `agent/` | `/opt/hja` (ro) | prompts, skills, `SOUL.md`, helper scripts | yes |
| `~/scout/materials` | `/opt/data/materials` (ro) | CV, past applications, `criteria.md`, `sources.md`, `guides/` | no |
| `~/scout/out` | `/opt/data/scout` | `drafts/`, `briefs/`, `plans/`, `applications.md`, `debriefs.md`, `preferences.md`, `seen.md` | no |
| `~/.hermes` | `/opt/data` | Hermes config, `.env` secrets, skills, memory, sessions, cron state, Claude login | no |
| repo `.env`, `secrets.env` | — | dashboard password, UID/GID, image tag; API keys before `make configure` | no (gitignored) |

The image contains only software. Everything personal lives in those folders: it survives rebuilds and updates, and moving to another machine means copying them.

Hermes runs as **your** UID (`HERMES_UID`/`HERMES_GID`, set by `make init`), so every file it writes on the host is owned by you: no `sudo`, no ACLs.

## Request flow of a scout run

1. The scheduler fires `scout`. If a mailbox is configured, `fetch_alerts.py` runs first and its output is prepended to the prompt.
2. The agent loads `scout-profile` and `scout-tracker`, reads `sources.md`, and searches (Brave).
3. For each new candidate (not in `seen.md` or `applications.md`) it opens the listing (Tavily, or Chromium for scripted pages) and confirms deadline, eligibility and how to apply.
4. It scores against the rubric, writes drafts for 75+, and updates the tracker.
5. The final answer goes to Telegram. `[SILENT]` suppresses delivery when nothing new scores 60+.

## Security model

| Measure | What it protects against |
|---|---|
| No outbound actions: `SOUL.md`, the skills and the prompts forbid sending, submitting or paying, and no mail-sending credentials exist | The agent acting on your behalf |
| Terminal and code-execution toolsets disabled on `cli`, `telegram` and `cron` (`make configure`) | Arbitrary command execution, e.g. after a prompt injection |
| Web pages and emails explicitly treated as data | Prompt injection through listings or alert emails |
| Materials and repo assets mounted read-only | The agent altering your CV, criteria, prompts or its own rules |
| Mailbox read by a script, not by the agent; `SCOUT_IMAP_*` instead of `EMAIL_*` | Emails becoming instructions via Hermes' email gateway |
| `TELEGRAM_ALLOWED_USERS` | Strangers using your bot |
| Dashboard bound to `127.0.0.1`, password-protected | Network access to the control plane |
| Unprivileged user, SELinux labels (`:Z`), resource limits | Escape from the mounted folders; runaway memory or CPU use |
| Free-tier API keys only | Cost of a leaked key |

Residual risk: the agent can read its own `.env` and has internet access, so a sufficiently clever injected page could try to exfiltrate those keys. Keep them free-tier and rotate them if in doubt. A container shares the host kernel; for stronger isolation run it on a dedicated server or VM.
