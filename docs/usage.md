# Daily use

## In Telegram

| You send | What happens |
|---|---|
| *(nothing)* | Every 12 h: new matches, highest score first, top matches (85+) under "Top matches — apply?". Silent if nothing new scores 60+. |
| a job link, optionally with "track this" or "draft" | Opened, verified, scored and added to the tracker; drafts written if it scores 60+ or you say "draft". |
| `apply <slug>` | Status "planned"; drafts checked; CV tailoring notes written; deadline reminders start (14, 7, 3 and 1 days before). |
| `skip <slug>` | Status "dropped"; never suggested again. |
| `applied to X` · `interview at Y` · `rejected from Z` · `offer from W` | Status and date updated; for interviews, rejections and offers the bot asks two quick debrief questions (how far it got, any feedback). |
| `status` | Open applications by deadline, plus counts per status. |
| `how am I doing?` · `what should I focus on?` | Career advisor: an honest review of your pipeline and where effort pays off. |
| `review my CV for <slug>` | CV tailoring notes for that opening. |
| `plan` · `what should I do next?` | Strategist: the current three-month plan, updated for anything new. |
| `note: <impression>` | A reflection on a place, role or experience, logged in `preferences.md` for future plans. |
| `radar` · `who cites me?` · `which labs should I watch?` | Research radar: latest digest and the labs watchlist. |
| `calls` · `short stays in <country>?` | Calls radar: visiting positions, short fellowships, schools, workshop calls, travel grants. |
| `visa <country>` | Mobility: routes, requirements, your estimated standing, recent changes. |
| `draft an email to … about …` | An email draft appears in the scout mailbox's Drafts folder within minutes; you review and send it. |
| `subscribe the mailbox to <site> alerts for <topic>` | The agent sets up the alert in its browser and confirms the subscription email when it arrives. |

## Files

| File | Contents |
|---|---|
| `~/scout/out/applications.md` | The tracker: one row per opportunity, with status history in the notes. |
| `~/scout/out/drafts/<slug>/cover_letter.md` | Draft cover letter. Edit it before use. |
| `~/scout/out/drafts/<slug>/checklist.md` | Required documents and submission steps. |
| `~/scout/out/drafts/<slug>/cv_notes.md` | How to tailor your CV for this opening: requirements, your evidence, gaps, what to reorder or cut. Your CV itself is never changed. |
| `~/scout/out/briefs/<date>.md` | Weekly market briefs. |
| `~/scout/out/plans/<YYYY-MM>.md` | Monthly three-month plans. |
| `~/scout/out/preferences.md` | Your axes, current leanings and dated reflections. Edit it freely. |
| `~/scout/out/debriefs.md` | One line per outcome: stage reached, feedback, your read. |
| `~/scout/out/radar/digests/<date>.md` · `radar/labs.md` | Daily radar digests; the watchlist of labs active in your area. |
| `~/scout/out/mobility/<country>.md` | Visa and residency routes with official sources, your estimated standing, changes since the last check. |
| `~/scout/out/outbox/` | Drafts waiting to be placed in the mailbox; `outbox/done/` once they are. |
| `~/scout/out/seen.md` | Everything already assessed, so nothing is reported twice. |

## Career advisor

The `career-advisor` skill adds three things:

- **Weekly market brief** (Mondays 08:00 in `HJA_TIMEZONE`; `make brief` for one now): 3–5 hiring and funding signals from the last 30 days, each with a source and date, what they mean for your profile, at most three actions for the week, and your pipeline at a glance.
- **CV tailoring notes** whenever you say `apply <slug>`.
- **Coaching on demand**: ask in Telegram. Answers are based on your tracker, profile and the latest brief, and separate evidence ("source, date") from the advisor's own judgement.

Put CV or application guides you trust in `~/scout/materials/guides/`; the advisor follows them over its general advice.

## Strategist

Once a month (the 1st, 09:00 in `HJA_TIMEZONE`; `make strategy` for one now) the `strategist` skill writes a three-month plan from everything it knows: your CV, the tracker, debriefs, market briefs and `preferences.md`.

It assumes you are **exploring**: still finding out where you want to live, through fixed-term moves rather than one big commitment. So the plan is a short sequence of experiments, each a role type × place, with why it was chosen, what it would teach you and how you'll know. It also gives an application mix (safe / realistic / stretch), at most three skills worth building, what to stop doing, and up to three questions whose answers sharpen the next plan.

Options are weighed on three axes, financial return, mobility/optionality and geography, without fixed weights: your leanings and dated reflections in `preferences.md` decide, newer ones counting more. Two habits make the plans better over time:

- **Answer the debrief questions** after each outcome, even with one line. Patterns need outcomes with reasons.
- **Send reflections** after visits, interviews or moves: `note: liked the pace in X, cost of living too high`.

With few outcomes the plan says its patterns are tentative and leans on your profile and the market; it gets sharper as data accumulates.

## Research radar

Every morning (07:00) a script collects new arXiv papers matching the queries in `radar.json` and, with an OpenAlex key and your author ID, new works citing your papers. The agent then reports:

- **every citation** of your work, with which paper it builds on and whether the authors look like collaborators;
- the few **relevant new papers**, labelled *overlap*, *builds on* or *useful*;
- **labs worth watching**, kept in `radar/labs.md`; once a lab in one of your target countries shows up three times, it suggests adding its page to `sources.md`.

Quiet days stay silent. The script asks arXiv for one query every few seconds, as arXiv's API terms require, and never re-reports a paper.

## Calls radar

Every Wednesday (08:00) the calls radar checks the programme pages, venues and queries in `calls.md`, plus the visiting pages of labs on your watchlist, for things that aren't job ads: visiting positions, short fellowships, summer schools, workshop calls, travel grants. Each item is confirmed on its own page (deadline, duration, eligibility, funding), scored with extra weight for **exploration value** (a target country you haven't tried yet), and added to the tracker with a kind tag such as `[visit]` or `[school]`. Say `apply <slug>` as usual to get drafts and deadline reminders.

## Mobility intelligence

On the 15th of each month the mobility check researches, from **official government sources only**, the work-permit, talent and residency routes for each country in your location order, and estimates your standing from the *Mobility facts* in `criteria.md` and your CV (for points systems, with the breakdown). It reports what changed since the last check and what would improve your standing. Estimates, not legal advice: confirm with the authority before acting.

## Mailbox (drafts only)

With a scout mailbox configured ([setup](setup.md#optional-scout-mailbox-drafts-only)):

- **Incoming mail** is read at every scout run: alerts become candidates, confirmations for subscriptions you asked for are confirmed, and replies from people are summarised in the report (never answered by the agent). Processed mail is labelled `HJA/processed` and archived.
- **Drafts**: ask for an email, or say `apply <slug>` for an opening that asks for applications by email. The agent writes the draft (with your CV attached when relevant), and within 5 minutes it is in the mailbox's Drafts folder with a Telegram note. Open it, edit, send.
- **Nothing is ever sent by the agent.** There is no SMTP in this setup at all, so it isn't a rule the agent could break; the capability doesn't exist.

## Teaching it

The model doesn't change. Hermes improves by writing things down, and scheduled runs start fresh, so **feedback only sticks once it is in a skill**:

1. Tell the bot what to change, e.g. *"Cover letters: under 350 words, open with the overlap with the PI's recent papers, never list my publications."*
2. Add: *"Update the scout-profile skill with this."*
3. Check the file: `~/.hermes/skills/hja/scout-profile/SKILL.md`.

Changes to `criteria.md` work the same way: edit the file, then run `make profile` to rebuild the skill.

## Customising

| Change | How |
|---|---|
| Criteria, CV, writing samples | Edit `~/scout/materials/`, then `make profile`. |
| Sites and queries | Edit `~/scout/materials/sources.md`. Picked up on the next run. |
| Radar queries, citation tracking | Edit `~/scout/materials/radar.json`. |
| Calls sources | Edit `~/scout/materials/calls.md`. |
| Preferences and location order | Edit `~/scout/out/preferences.md` (read by every plan). Keep the location priority in `criteria.md` in step, then `make profile`. |
| What each run does | Edit `agent/prompts/scout.md` or `deadlines.md`, then `make jobs`. |
| Tracker behaviour | Edit `agent/skills/scout-tracker/SKILL.md`, then `make install`. |
| Standing rules | Edit `agent/SOUL.md`, then `make install && make restart`. |
| Schedule | Change `every 12h` / `every 24h` in `agent/scripts/jobs.sh`, then `make jobs`. |
